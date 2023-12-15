def ensure_map_public(conn, module, subnet, map_public, check_mode, start_time):
    if check_mode:
        return
    try:
        conn.modify_subnet_attribute(SubnetId=subnet['id'], MapPublicIpOnLaunch={'Value': map_public})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't modify subnet attribute")