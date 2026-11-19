#!/usr/bin/env python
"""
Download pre-trained blocking detection model.

This script downloads the U-Net/ResNet152 model trained for atmospheric
blocking detection from the PCMDI data server.

Usage:
    download_blocking_model.py [--output-path PATH] [--version VERSION]

Examples:
    # Download to default location
    download_blocking_model.py

    # Download to custom location
    download_blocking_model.py --output-path /path/to/models

    # Specify model version
    download_blocking_model.py --version oct11
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests package required. Install with:")
    print("  conda install requests")
    print("  or: pip install requests")
    sys.exit(1)


# Model information
MODEL_VERSIONS = {
    "oct11": {
        "filename": "falco_fulldata_oct11.h5",
        "url": "https://pcmdi.llnl.gov/pss/pmpdata/blocking_pre-trained-model/falco_fulldata_oct11.h5",
        "size_mb": 246,
        "description": "October 2023 version - U-Net with ResNet152 backbone",
    }
}

DEFAULT_VERSION = "oct11"


def get_default_output_path():
    """Determine default output path for model file."""
    # Check if in conda environment
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        return os.path.join(conda_prefix, "share", "pmp", "blocking_models")

    # Fall back to package location if installed
    try:
        import pcmdi_metrics

        pkg_path = os.path.dirname(pcmdi_metrics.__file__)
        return os.path.join(pkg_path, "..", "share", "pmp", "blocking_models")
    except ImportError:
        pass

    # Fall back to user home directory
    return os.path.join(Path.home(), ".pcmdi_metrics", "blocking_models")


def download_file(url, output_path, chunk_size=8192):
    """
    Download file with progress bar.

    Parameters
    ----------
    url : str
        URL to download from.
    output_path : str
        Local file path to save to.
    chunk_size : int
        Download chunk size in bytes.

    Returns
    -------
    bool
        True if download succeeded, False otherwise.
    """
    try:
        print(f"Downloading from: {url}")
        print(f"Saving to: {output_path}")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get file size if available
        total_size = int(response.headers.get("content-length", 0))

        # Download with progress
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(
                            f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)",
                            end="",
                        )

        print("\nDownload complete!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\nError downloading file: {e}")
        return False


def verify_file_size(file_path, expected_size_mb, tolerance=5):
    """
    Verify downloaded file size is reasonable.

    Parameters
    ----------
    file_path : str
        Path to downloaded file.
    expected_size_mb : float
        Expected file size in MB.
    tolerance : float
        Tolerance in MB.

    Returns
    -------
    bool
        True if file size is within tolerance.
    """
    if not os.path.exists(file_path):
        return False

    actual_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    diff = abs(actual_size_mb - expected_size_mb)

    if diff > tolerance:
        print(
            f"Warning: File size ({actual_size_mb:.1f} MB) differs from "
            f"expected ({expected_size_mb:.1f} MB) by {diff:.1f} MB"
        )
        return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download pre-trained blocking detection model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download to default location
  %(prog)s

  # Download to custom location
  %(prog)s --output-path /path/to/models

  # Specify model version
  %(prog)s --version oct11

Default download location:
  - If in conda env: $CONDA_PREFIX/share/pmp/blocking_models/
  - Otherwise: ~/.pcmdi_metrics/blocking_models/
        """,
    )

    parser.add_argument(
        "--output-path",
        help="Output directory path. If not specified, uses default location.",
        default=None,
    )

    parser.add_argument(
        "--version",
        help=f"Model version to download. Default: {DEFAULT_VERSION}",
        default=DEFAULT_VERSION,
        choices=list(MODEL_VERSIONS.keys()),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if file already exists.",
    )

    args = parser.parse_args()

    # Get model information
    model_info = MODEL_VERSIONS[args.version]
    model_filename = model_info["filename"]
    model_url = model_info["url"]
    expected_size = model_info["size_mb"]

    # Determine output path
    if args.output_path is None:
        output_dir = get_default_output_path()
    else:
        output_dir = args.output_path

    output_file = os.path.join(output_dir, model_filename)

    # Print information
    print("=" * 70)
    print("PCMDI Metrics - Blocking Detection Model Download")
    print("=" * 70)
    print(f"Version: {args.version}")
    print(f"Description: {model_info['description']}")
    print(f"Size: ~{expected_size} MB")
    print(f"Output directory: {output_dir}")
    print("=" * 70)

    # Check if file already exists
    if os.path.exists(output_file) and not args.force:
        print(f"\nModel file already exists: {output_file}")

        # Verify size
        if verify_file_size(output_file, expected_size):
            print("File size verified. Download not needed.")
            print("\nTo force re-download, use --force flag.")
            return 0
        else:
            print("File size verification failed. Re-downloading...")

    # Create output directory
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Cannot create output directory: {e}")
        return 1

    # Download file
    print("\nStarting download...")
    success = download_file(model_url, output_file)

    if not success:
        print("\nDownload failed!")
        return 1

    # Verify file
    if verify_file_size(output_file, expected_size):
        print("\nFile size verified successfully.")
    else:
        print(
            "\nWarning: Downloaded file size differs from expected. "
            "Please verify the download completed correctly."
        )

    print("\n" + "=" * 70)
    print("SUCCESS! Model downloaded to:")
    print(f"  {output_file}")
    print("=" * 70)
    print("\nYou can now use the blocking metrics:")
    print("  from pcmdi_metrics.blocking import detect_blocking")
    print("  blocking = detect_blocking(ds, var='zg')")

    return 0


if __name__ == "__main__":
    sys.exit(main())
