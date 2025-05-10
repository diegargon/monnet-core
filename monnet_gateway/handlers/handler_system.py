from monnet_gateway.services.ansible_service import AnsibleService


def handle_system_command(ctx, command, data):
    """
    Handle system-level commands like restart, shutdown, etc.

    Args:
        ctx (AppContext): Application context.
        command (str): Command name.
        data (dict): Additional data for the command.

    Returns:
        dict: Response dictionary.
    """
    logger = ctx.get_logger()

    if command == "restart_daemon":
        logger.info("Restart command received. Restarting daemon...")
        # This would work only if systemd is used and set to restart always
        ctx.get_var('stop_event').set()
        return {"status": "success", "message": "Daemon is restarting"}
    elif command == "reload_pb_metadata":
        logger.info("Reloading Playbook metadata...")
        ansibleService = AnsibleService(ctx)
        ansibleService.extract_pb_metadata()
        return {"status": "success", "message": "Playbook metadata reloaded"}
    elif command == "reload_config":
        logger.info("Reloading configuration...")
        config = ctx.get_config()
        config.reload()
        return {"status": "success", "message": "Configuration reloaded"}
    else:
        return {"status": "error", "message": f"Unknown system command: {command}"}





