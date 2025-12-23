const childProcess = require('node:child_process');
const fs = require("node:fs/promises");
const { uniq } = require('lodash')

const httpApiFunctions = Object
    .values(serverless.service.functions)
    .filter(value => value
        .events
        ?.some(evt => evt.httpApi !== undefined)
    )

/**
 * @param {string[]} paths - paths to the lambda handlers
 * @returns {Promise<{ endpoints: Record<string, {
 *  responseNames: string[];
 *  body: any;
 *  queryParams: any;
 *  pathParams: any;
 *  operationId: string | null | undefined,
 *  description: string | null | undefined,
 *  summary: string | null | undefined,
 *  tags: string[]
 * }>, tags: { name: string, description: string }[], models: any}>}
 */
const getPythonHandlerDataForPaths = async (paths) => (
    JSON.parse(await new Promise((resolve, reject) => childProcess.exec(
        "uv run get_function_openapi_metadata.py " + paths.join(" "),
        (error, stdout) => {
            if (error) {
                reject(error)
            } else {
                resolve(stdout)
            }
        }
    )))
);

const getHttpResponseCodeFromSchema = (schema) => {
    const code = schema.properties?.statusCode?.const ?? schema.properties?.status_code?.const;

    if (code === undefined) {
        throw new Error(`Could determine the status code from response schema (code not const?) for response type ${schema.title}`)
    }

    return code.toString();
}

/**
 * @param {string} name
 * @returns {import("openapi-types").OpenAPIV3_1.ResponseObject}
 */
const getResponseObjectFromSchema = (name, schema) => ({
    description: schema.properties.body?.description ?? schema.properties.body?.default ?? schema.title,
    content: '$ref' in schema.properties.body ? {
        ['application/json']: {
            schema: {
                $ref: `#/components/schemas/${name}`
            }
        }
    } : {
        ['text/plain']: {
            schema: {
                type: 'string'
            }
        }
    }
})

/**
 * @param {any} schema
 * @param {"query" | "path"} type
 * @param {string} operationId
 */
const getParameters = (schema, type, operationId) => schema ? Object.entries(schema.properties).map(([propName, propDef]) => {
    if (["array", "object"].includes(propDef.type)) {
        console.warn(`Invaild endpoint parameter type "${propDef.type}" for ${propName} (${type}) in ${operationId}`)
        return;
    }

    /** @type{import("openapi-types").OpenAPIV3.ParameterObject} */
    const result = {
        in: type,
        name: propName,
        required: schema.required.includes(propName),
        allowEmptyValue: false,
        description: propDef.description,
        schema: propDef,
    }

    return result;
}).filter(x => !!x) : [];

/**
 * @param {Awaited<ReturnType<typeof getPythonHandlerDataForPaths>>['endpoints'][string] } endpointData
 */
const getResponsesObject = (models, endpointData, fnData) => {
    const modelSchemas = endpointData.responseNames.map(name => ({ name, schema: models.$defs[name] }));

    if (modelSchemas.some(({ schema }) => !schema)) {
        throw new Error("Some response schemas were not found by name");
    }

    const responsesArr = modelSchemas.map(({ name, schema }) => [getHttpResponseCodeFromSchema(schema), getResponseObjectFromSchema(name, schema)]);

    if (new Set(responsesArr.map(([code]) => code)).size !== responsesArr.length) {
        throw new Error(`Duplicate response code models defined for ${fnData.handler}`);
    }

    return Object.fromEntries(responsesArr);
}

/**
 * @param {(data: any, prop: string | number) => boolean} callback
 */
const forEachDeep = (data, callback) => {
    if (typeof data !== 'object') {
        return;
    }

    if (Array.isArray(data)) {
        for (const item of data) {
            forEachDeep(item, callback);
        }
        return;
    }

    if (callback(data))
        return;

    if (data !== undefined && data !== null) {
        for (const prop of Object.keys(data)) {
            forEachDeep(data[prop], callback);
        }
    }
}

const updateModelRefs = (data) => {
    if (typeof data !== 'object') {
        return;
    }

    if (Array.isArray(data)) {
        for (const item of data) {
            updateModelRefs(item);
        }
        return;
    }

    if (typeof data?.$ref === 'string') {
        const modelName = data.$ref.split('/').at(-1);

        if (!modelName) {
            return;
        }

        data.$ref = `#/components/schemas/${modelName}`
        return
    }

    if (data !== undefined && data !== null) {
        for (const prop of Object.keys(data)) {
            updateModelRefs(data[prop]);
        }
    }
}

const getSecuritySchemes = () => {
    const httpApiEvents = httpApiFunctions
        .flatMap(fn => fn.events)
        .filter(evt => evt.httpApi)

    const uniqueAuthorizerNames = uniq(
        httpApiEvents
            .filter(evt => evt.httpApi.authorizer?.id?.Ref ?? evt.httpApi.authorizer?.name)
            .map(evt => evt.httpApi.authorizer?.id?.Ref ?? evt.httpApi.authorizer?.name)
    );

    return Object.fromEntries(
        uniqueAuthorizerNames.map(name => {
            // const authorizerObject = serverless.service.resources.Resources[name];

            // if (!authorizerObject) {
            //     throw new Error(`Authorizer not found: ${name}`);
            // }

            /** @type{import("openapi-types").OpenAPIV3_1.SecuritySchemeObject} */
            const scheme = {
                type: 'apiKey',
                name: "Authorization",
                in: 'header'
            };

            return [name, scheme];
        })
    )
}

const custom = serverless.service.custom;
const openApiConfig = custom.openapi;

(async () => {
    try {
        const handlerData = await getPythonHandlerDataForPaths(httpApiFunctions.map(fn => fn.handler))

        try {
            /** @type{import("openapi-types").OpenAPIV3_1.Document} */
            const definition = {
                openapi: "3.1.0",
                info: {
                    title: openApiConfig.info.title,
                    version: openApiConfig.info.version,
                    description: openApiConfig.info.description,
                },
                servers: [
                    { url: `https://${custom.customDomain.domainName}` }
                ],
                paths: Object.fromEntries(
                    httpApiFunctions
                        .flatMap(fn => fn.events
                            .filter(evt => evt.httpApi)
                            .map(evt => {
                                const data = handlerData.endpoints[fn.handler];

                                if (!data)
                                    return null;

                                /** @type{Exclude<Exclude<import("openapi-types").OpenAPIV3_1.Document['paths'], undefined>[string], undefined>} */
                                const endpoint = {
                                    [evt.resolvedMethod.toLowerCase()]: {
                                        description: data.description,
                                        summary: data.summary,
                                        operationId: data.operationId,
                                        responses: getResponsesObject(handlerData.models, data, fn),
                                        security: [
                                            { [evt.httpApi.authorizer?.id?.Ref ?? evt.httpApi.authorizer?.name]: [] }
                                        ],
                                        requestBody: data.body ? {
                                            content: {
                                                'application/json': { schema: data.body },
                                            }
                                        } : undefined,
                                        parameters: [
                                            ...getParameters(data.pathParams, 'path', data.operationId),
                                            ...getParameters(data.queryParams, 'query', data.operationId),
                                        ],
                                        tags: data.tags
                                    }
                                }

                                return ([evt.resolvedPath, endpoint]);
                            })
                        )
                        .filter(x => x !== null)
                ),
                tags: handlerData.tags,
                components: {
                    schemas: handlerData.models.$defs,
                    securitySchemes: getSecuritySchemes(),
                }
            }

            forEachDeep(definition, (data) => {
                if (typeof data?.$ref === 'string') {
                    const modelName = data.$ref.split('/').at(-1);

                    if (!modelName) {
                        throw new Error(`Invalid $ref "${data.$ref}"`);
                    }

                    data.$ref = `#/components/schemas/${modelName}`
                    return true;
                }

                return false;
            });

            forEachDeep(definition, (data) => {
                if (typeof data?.$defs === 'object') {
                    for (const [name, schema] of Object.entries(data.$defs)) {
                        if (!definition.components.schemas[name]) {
                            definition.components.schemas[name] = schema;
                        } else if (JSON.stringify(schema) !== JSON.stringify(definition.components.schemas[name])) {
                            console.warn(`Two differing schemas found for "${name}"`)
                        }
                    }

                    delete data.$defs;

                    return true;
                }

                return false;
            })

            await fs.writeFile('.serverless/openapi.json', JSON.stringify(definition, null, 4));

            console.log('Openapi definition generated successfully');
        } catch (e) {
            console.error("Failed to generate the spec", e);
            process.exit(1);
        }
    } catch (e) {
        console.error("Failed to get the endpoint data", e);
        process.exit(1);
    }
})()

