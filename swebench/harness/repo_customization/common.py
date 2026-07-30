import json


def _build_google_services_json(package_names: list[str]) -> str:
    """Build a valid google-services.json with client entries for each package name."""
    clients = []
    for pkg in package_names:
        clients.append({
            "client_info": {
                "mobilesdk_app_id": "1:123456789000:android:abcdef1234567890",
                "android_client_info": {"package_name": pkg},
            },
            "api_key": [{"current_key": "AIzaSyPlaceholderKeyForBuildOnly000"}],
        })
    return json.dumps(
        {
            "project_info": {
                "project_number": "123456789000",
                "project_id": "placeholder-project",
                "storage_bucket": "placeholder-project.appspot.com",
            },
            "client": clients,
            "configuration_version": "1",
        },
        indent=2,
    )


def google_services_commands(entries: list[tuple[str, str | list[str]]]) -> list[str]:
    """Generate bash commands to write valid google-services.json files.

    entries: list of (directory_path, package_names) tuples.
        package_names can be a single string or a list of strings for repos
        with multiple product flavors.

    For each base package name, a '.debug' variant is automatically included
    since the instance build always runs ``./gradlew assembleDebug``.
    """
    commands = []
    for dir_path, pkg in entries:
        base_names = [pkg] if isinstance(pkg, str) else pkg
        all_names = []
        for name in base_names:
            all_names.append(name)
            all_names.append(f"{name}.debug")
        json_content = _build_google_services_json(all_names)
        commands.append(
            f"mkdir -p {dir_path} && cat > {dir_path}/google-services.json << 'GSEOF'\n"
            f"{json_content}\n"
            f"GSEOF"
        )
    return commands
