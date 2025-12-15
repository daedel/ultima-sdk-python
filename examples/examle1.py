import os
from ultima_sdk.files import Files

def ensure_uo_directory():
  # Try auto-discover; don't fail hard if it raises
  try:
    Files.initialize()
  except Exception:
    pass

  # Check if a known file can be resolved
  def has_known_file():
    try:
      art_path = Files.get_file_path("art.mul")
    except Exception:
      return False
    return bool(art_path and os.path.exists(art_path))

  if not has_known_file():
    # Prompt user until a valid UO directory is provided
    while True:
      try:
        user_dir = input("Ultima Online directory not found. Please enter the path to your UO client: ").strip()
      except (KeyboardInterrupt, EOFError):
        raise SystemExit("UO directory is required to continue.")

      if not user_dir:
        continue
      if not os.path.isdir(user_dir):
        print("Path does not exist or is not a directory. Try again.")
        continue

      # Basic validation for common UO files
      valid = any(os.path.exists(os.path.join(user_dir, fn)) for fn in ("art.mul", "client.exe", "ultima.exe"))
      if not valid:
        print("Directory doesn't contain expected UO files (e.g. art.mul). Try again.")
        continue

      # Set directory in SDK and export to environment
      Files.set_directory(user_dir)
      os.environ["UO_ROOT"] = user_dir

      # Re-run initialize in case SDK needs it
      try:
        Files.initialize()
      except Exception:
        pass

      if has_known_file():
        break
      else:
        print("Could not verify files after setting directory. Try again.")

ensure_uo_directory()

# Get file paths
art_path = Files.get_file_path("art.mul")
print("art.mul path:", art_path)