import os
import zipfile


def package_sdk():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    frontend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend")
    )

    if not os.path.exists(frontend_dir):
        os.makedirs(frontend_dir)

    output_zip = os.path.join(frontend_dir, "secure_document_vault.zip")

    print(f"Packing SDK from {src_dir} to {output_zip}...")

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(src_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py") or file == "py.typed":
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, src_dir)
                    zipf.write(file_path, arcname)

    print("Packing successful.")


if __name__ == "__main__":
    package_sdk()
