def child_folder_name(parent_path: str, folder: str) -> str | None:
    rest = parent_path
    if folder:
        prefix = f"{folder}/"
        if not parent_path.startswith(prefix):
            return None
        rest = parent_path[len(prefix) :]
    if not rest:
        return None
    return rest.split("/", 1)[0]


def child_folder_names(parent_paths: list[str], folder: str) -> list[str]:
    names = {name for parent in parent_paths if (name := child_folder_name(parent, folder))}
    return sorted(names)
