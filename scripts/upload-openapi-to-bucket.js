const fs = require('fs/promises');

const provider = serverless.getProvider('aws');

(async () => {
    try {
        if (!serverless.service.custom?.openapi?.bucket?.name || serverless.service.custom?.openapi?.bucket?.key) {
            console.warn("Openapi bucket name or key not set, skipping upload")
            return;
        }

        const contents = fs.readFile('.serverless/openapi.json');

        const params = {
            Bucket: serverless.service.custom.openapi.bucket.name,
            Key: serverless.service.custom.openapi.bucket.key,
            Body: contents,
            ContentType: 'application/json',
        }

        await provider.request('S3', 'putObject', params);
    } catch (e) {
        console.error('Failed to upload the openapi description to bucket', e)
        process.exit(1);
    }
})()
