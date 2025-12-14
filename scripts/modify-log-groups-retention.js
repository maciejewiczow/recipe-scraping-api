const logRetentionDays = serverless.service.custom?.logging?.logGroupsRetentionInDays;

if (logRetentionDays) {
    for (
        const logGroup of Object
            .values(serverless.service.provider.compiledCloudFormationTemplate.Resources)
            .filter(resource => resource.Type === 'AWS::Logs::LogGroup')
            .filter(lg => !lg.Properties?.RetentionInDays)
    ) {
        logGroup.Properties.RetentionInDays = logRetentionDays;
    }
}
