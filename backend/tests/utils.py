"""
Test utility functions for vehicle controller test analysis system
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile
import shutil


def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
    """
    Calculate hash of a file

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256)

    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def compare_files(file1: Path, file2: Path) -> bool:
    """
    Compare two files byte by byte

    Args:
        file1: Path to first file
        file2: Path to second file

    Returns:
        True if files are identical, False otherwise
    """
    if not file1.exists() or not file2.exists():
        return False

    if file1.stat().st_size != file2.stat().st_size:
        return False

    return calculate_file_hash(file1) == calculate_file_hash(file2)


def compare_json_files(file1: Path, file2: Path) -> bool:
    """
    Compare two JSON files (order-insensitive)

    Args:
        file1: Path to first JSON file
        file2: Path to second JSON file

    Returns:
        True if JSON content is equal, False otherwise
    """
    try:
        with open(file1, "r", encoding="utf-8") as f:
            data1 = json.load(f)

        with open(file2, "r", encoding="utf-8") as f:
            data2 = json.load(f)

        return data1 == data2
    except Exception:
        return False


def validate_data_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that a dictionary contains all required fields

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        True if all fields present, False otherwise
    """
    return all(field in data for field in required_fields)


def validate_can_message(message: Dict[str, Any]) -> bool:
    """
    Validate CAN message structure

    Args:
        message: CAN message dictionary

    Returns:
        True if valid, False otherwise
    """
    required = ["timestamp", "message_id", "dlc", "data"]
    return validate_data_structure(message, required) and len(message["data"]) == message["dlc"]


def validate_parsed_signal(signal: Dict[str, Any]) -> bool:
    """
    Validate parsed signal structure

    Args:
        signal: Signal dictionary

    Returns:
        True if valid, False otherwise
    """
    required = ["signal_name", "signal_value", "unit"]
    return validate_data_structure(signal, required)


def compare_signals(
    signal1: Dict[str, Any],
    signal2: Dict[str, Any],
    tolerance: float = 0.01
) -> bool:
    """
    Compare two signal values with tolerance

    Args:
        signal1: First signal
        signal2: Second signal
        tolerance: Tolerance for numeric comparison

    Returns:
        True if signals match within tolerance
    """
    if signal1.get("signal_name") != signal2.get("signal_name"):
        return False

    val1 = signal1.get("signal_value")
    val2 = signal2.get("signal_value")

    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        return abs(val1 - val2) <= tolerance

    return val1 == val2


def create_temp_copy(source: Path, temp_dir: Optional[Path] = None) -> Path:
    """
    Create a temporary copy of a file

    Args:
        source: Source file path
        temp_dir: Optional custom temp directory

    Returns:
        Path to temporary copy
    """
    if temp_dir is None:
        temp_dir = Path(tempfile.gettempdir())

    temp_file = temp_dir / f"temp_{source.name}"
    shutil.copy2(source, temp_file)

    return temp_file


def read_lines(file_path: Path, max_lines: Optional[int] = None) -> List[str]:
    """
    Read lines from a file

    Args:
        file_path: Path to file
        max_lines: Maximum number of lines to read (None = all)

    Returns:
        List of lines
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if max_lines is not None:
        lines = lines[:max_lines]

    return lines


def count_lines(file_path: Path) -> int:
    """
    Count lines in a file

    Args:
        file_path: Path to file

    Returns:
        Number of lines
    """
    return len(read_lines(file_path))


def validate_csv_structure(file_path: Path, required_columns: List[str]) -> bool:
    """
    Validate CSV file has required columns

    Args:
        file_path: Path to CSV file
        required_columns: List of required column names

    Returns:
        True if CSV has all required columns
    """
    import pandas as pd

    try:
        df = pd.read_csv(file_path, nrows=1)
        columns = df.columns.tolist()

        # Remove whitespace from column names
        columns = [col.strip() for col in columns]

        return all(col in columns for col in required_columns)
    except Exception:
        return False


def validate_dbc_file(file_path: Path) -> bool:
    """
    Validate DBC file has basic required structure

    Args:
        file_path: Path to DBC file

    Returns:
        True if DBC appears valid
    """
    required_keywords = [
        "VERSION",
        "NS_",
        "BS_",
        "BO_"
    ]

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return all(keyword in content for keyword in required_keywords)
    except Exception:
        return False


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Get detailed file information

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    stat = file_path.stat()

    return {
        "name": file_path.name,
        "size": stat.st_size,
        "extension": file_path.suffix,
        "exists": file_path.exists(),
        "is_file": file_path.is_file(),
        "hash_md5": calculate_file_hash(file_path, "md5") if file_path.exists() else None
    }


def create_test_project_data() -> Dict[str, Any]:
    """
    Create test project data

    Returns:
        Project data dictionary
    """
    return {
        "name": "Test Project",
        "description": "Automated test project",
        "created_at": "2024-03-17T10:00:00",
        "dbc_file_id": None
    }


def assert_response_success(response: Any, expected_status: int = 200) -> Dict[str, Any]:
    """
    Assert API response is successful and return JSON data

    Args:
        response: TestClient response object
        expected_status: Expected HTTP status code

    Returns:
        Response JSON data

    Raises:
        AssertionError: If response is not successful
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json()

    # Check for error response format
    if "error" in data:
        raise AssertionError(f"API returned error: {data['error']}")

    return data


def measure_execution_time(func) -> tuple:
    """
    Measure execution time of a function

    Args:
        func: Function to measure

    Returns:
        Tuple of (result, execution_time_ms)
    """
    import time

    start_time = time.time()
    result = func()
    end_time = time.time()

    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

    return result, execution_time


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} TB"


def clean_temp_files(temp_dir: Path) -> int:
    """
    Clean all files in a temporary directory

    Args:
        temp_dir: Path to temporary directory

    Returns:
        Number of files deleted
    """
    deleted_count = 0

    for file in temp_dir.glob("*"):
        if file.is_file():
            try:
                file.unlink()
                deleted_count += 1
            except Exception:
                pass

    return deleted_count


def create_sample_csv(output_path: Path, num_rows: int = 100) -> None:
    """
    Create a sample CSV file for testing

    Args:
        output_path: Path to output CSV file
        num_rows: Number of rows to generate
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    timestamps = [datetime(2024, 3, 17) + timedelta(milliseconds=i*50) for i in range(num_rows)]

    data = {
        "timestamp": [t.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] for t in timestamps],
        "message_id": [100 + (i % 4) for i in range(num_rows)],
        "message_name": ["VCU_Status", "BMS_Data", "Motor_Torque", "MCU_Control"][::4] * (num_rows // 4 + 1),
        "signal_name": ["Test_Signal"] * num_rows,
        "signal_value": np.random.rand(num_rows) * 100,
        "unit": ["V"] * num_rows
    }

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
