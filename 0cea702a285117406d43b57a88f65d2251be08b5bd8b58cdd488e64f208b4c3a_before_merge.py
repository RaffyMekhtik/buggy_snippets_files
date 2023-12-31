    def __init__(self, metadata=None, thread_config=4, **kwargs):

        self.cloudformation = CloudFormationConfig(metadata['management']['cloudformation'], thread_config)
        self.cloudtrail = CloudTrailConfig(metadata['management']['cloudtrail'], thread_config)
        self.cloudwatch = CloudWatchConfig(metadata['management']['cloudwatch'], thread_config)
        self.directconnect = DirectConnectConfig(metadata['network']['directconnect'], thread_config)
        self.ec2 = EC2Config(metadata['compute']['ec2'], thread_config)
        self.efs = EFSConfig(metadata['storage']['efs'], thread_config)
        self.elasticache = ElastiCacheConfig(metadata['database']['elasticache'], thread_config)
        self.elb = ELBConfig(metadata['compute']['elb'], thread_config)
        self.elbv2 = ELBv2Config(metadata['compute']['elbv2'], thread_config)
        self.emr = EMRConfig(metadata['analytics']['emr'], thread_config)
        self.iam = IAMConfig(thread_config)
        self.kms = KMSConfig(metadata['security']['kms'], thread_config)
        self.awslambda = LambdaConfig(metadata['compute']['awslambda'], thread_config)
        self.redshift = RedshiftConfig(metadata['database']['redshift'], thread_config)
        self.rds = RDSConfig(metadata['database']['rds'], thread_config)
        self.route53 = Route53Config(thread_config)
        self.route53domains = Route53DomainsConfig(thread_config)
        self.s3 = S3Config(thread_config)
        self.ses = SESConfig(metadata['messaging']['ses'], thread_config)
        self.sns = SNSConfig(metadata['messaging']['sns'], thread_config)
        self.sqs = SQSConfig(metadata['messaging']['sqs'], thread_config)
        self.vpc = VPCConfig(metadata['network']['vpc'], thread_config)