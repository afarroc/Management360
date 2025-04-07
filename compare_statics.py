import os
import filecmp

def list_files(directory):
    """List all files in a directory recursively."""
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.relpath(os.path.join(root, file), directory))
    return file_paths

def compare_directories(dir1, dir2):
    """Compare files in two directories and find duplicates."""
    files1 = list_files(dir1)
    files2 = list_files(dir2)

    duplicates = []
    for file in files1:
        if file in files2:
            file1_path = os.path.join(dir1, file)
            file2_path = os.path.join(dir2, file)
            if filecmp.cmp(file1_path, file2_path, shallow=False):
                duplicates.append(file)
    return duplicates

if __name__ == "__main__":
    dir1 = "static"
    dir2 = "staticfiles"

    if not os.path.exists(dir1) or not os.path.exists(dir2):
        print(f"Error: One or both directories '{dir1}' and '{dir2}' do not exist.")
    else:
        duplicates = compare_directories(dir1, dir2)
        if duplicates:
            print("Duplicate files found:")
            for duplicate in duplicates:
                print(f" - {duplicate}")
        else:
            print("No duplicate files found.")
