# Standard library imports
import os

# Django imports
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_GET


@require_GET
def file_tree_view(request):
    """
    View to generate a file tree structure for a given app directory.
    
    Args:
        request: HttpRequest object with optional 'app_name' GET parameter
        
    Returns:
        JsonResponse with either:
        - List of all apps (if no app_name provided)
        - File tree structure for specified app
        - Error message if app doesn't exist
    """
    app_name = request.GET.get("app_name", "")

    if not app_name:
        # List all apps in the project if no app name is provided
        apps_dir = os.path.join(settings.BASE_DIR)
        apps = [
            {"name": app, "type": "directory"}
            for app in os.listdir(apps_dir)
            if os.path.isdir(os.path.join(apps_dir, app)) and not app.startswith("__")
        ]
        return JsonResponse(apps, safe=False)

    base_dir = os.path.join(settings.BASE_DIR, app_name)
    if not os.path.exists(base_dir):
        return JsonResponse(
            {"error": f"The app '{app_name}' does not exist or its directory is invalid."},
            status=400
        )

    # Recursively build the file tree
    def get_file_tree(directory):
        tree = []
        try:
            for entry in os.listdir(directory):
                entry_path = os.path.join(directory, entry)
                if os.path.isdir(entry_path):
                    tree.append({
                        "name": entry,
                        "type": "directory",
                        "path": os.path.relpath(entry_path, settings.BASE_DIR),
                        "children": get_file_tree(entry_path)
                    })
                else:
                    tree.append({
                        "name": entry,
                        "type": "file",
                        "path": os.path.relpath(entry_path, settings.BASE_DIR),
                        "size": os.path.getsize(entry_path)
                    })
        except PermissionError:
            pass  # Skip directories we can't access
        return tree

    file_tree = get_file_tree(base_dir)
    return JsonResponse(file_tree, safe=False)