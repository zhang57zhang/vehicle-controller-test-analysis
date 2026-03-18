"""
Integration tests for vehicle controller test analysis system
"""
import pytest
from pathlib import Path
from typing import Dict, Any
import json

from utils import (
    compare_files,
    validate_dbc_file,
    assert_response_success,
    measure_execution_time
)


@pytest.mark.integration
def test_complete_file_upload_flow(client, test_data_dir, temp_upload_dir):
    """
    Test complete file upload, parsing, and storage flow
    """
    # Upload CSV file
    csv_path = test_data_dir / "sample.csv"
    assert csv_path.exists(), "Test CSV file not found"

    with open(csv_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("sample.csv", f, "text/csv")}
        )

    upload_result = assert_response_success(response)
    assert "file_id" in upload_result
    file_id = upload_result["file_id"]

    # Verify file was stored
    get_response = client.get(f"/api/files/{file_id}")
    file_info = assert_response_success(get_response)

    assert file_info["filename"] == "sample.csv"
    assert file_info["file_type"] == "csv"


@pytest.mark.integration
def test_dbc_upload_and_parsing(client, test_data_dir):
    """
    Test DBC file upload and parsing
    """
    dbc_path = test_data_dir / "sample.dbc"
    assert dbc_path.exists(), "Test DBC file not found"
    assert validate_dbc_file(dbc_path), "DBC file appears invalid"

    # Upload DBC file
    with open(dbc_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("sample.dbc", f, "text/plain")}
        )

    upload_result = assert_response_success(response)
    file_id = upload_result["file_id"]

    # Parse DBC file
    parse_response = client.post(f"/api/dbc/parse/{file_id}")
    parse_result = assert_response_success(parse_response)

    assert "messages" in parse_result
    assert len(parse_result["messages"]) > 0

    # Verify known messages exist
    message_ids = [msg["id"] for msg in parse_result["messages"]]
    assert 100 in message_ids  # VCU_Status
    assert 200 in message_ids  # BMS_Data


@pytest.mark.integration
def test_project_creation_with_dbc(client, test_data_dir):
    """
    Test project creation and DBC file association
    """
    # Upload DBC first
    dbc_path = test_data_dir / "sample.dbc"
    with open(dbc_path, "rb") as f:
        dbc_response = client.post(
            "/api/files/upload",
            files={"file": ("sample.dbc", f, "text/plain")}
        )

    dbc_result = assert_response_success(dbc_response)
    dbc_file_id = dbc_result["file_id"]

    # Create project with DBC
    project_data = {
        "name": "Integration Test Project",
        "description": "Test project with DBC",
        "dbc_file_id": dbc_file_id
    }

    response = client.post("/api/projects/", json=project_data)
    project = assert_response_success(response)

    assert project["name"] == "Integration Test Project"
    assert project["dbc_file_id"] == dbc_file_id

    # Verify project has DBC file
    get_response = client.get(f"/api/projects/{project['id']}")
    project_details = assert_response_success(get_response)

    assert project_details["dbc_file"]["id"] == dbc_file_id


@pytest.mark.integration
def test_can_log_import_and_analysis(client, test_data_dir):
    """
    Test CAN log file import and basic analysis
    """
    log_path = test_data_dir / "sample.log"
    assert log_path.exists(), "Test log file not found"

    # Upload log file
    with open(log_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("sample.log", f, "text/plain")}
        )

    upload_result = assert_response_success(response)
    file_id = upload_result["file_id"]

    # Parse log file
    parse_response = client.post(f"/api/can/parse/{file_id}")
    parse_result = assert_response_success(parse_response)

    assert "messages" in parse_result
    assert len(parse_result["messages"]) > 0

    # Verify message structure
    first_message = parse_result["messages"][0]
    assert "timestamp" in first_message
    assert "message_id" in first_message
    assert "data" in first_message


@pytest.mark.integration
def test_data_export_functionality(client, sample_project):
    """
    Test data export in multiple formats
    """
    project_id = sample_project["id"]

    # Export to CSV
    csv_response = client.get(f"/api/projects/{project_id}/export/csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers.get("content-type", "")

    # Export to JSON
    json_response = client.get(f"/api/projects/{project_id}/export/json")
    assert json_response.status_code == 200
    assert "application/json" in json_response.headers.get("content-type", "")


@pytest.mark.integration
def test_data_query_and_filtering(client, test_data_dir, sample_project):
    """
    Test querying and filtering of imported data
    """
    project_id = sample_project["id"]

    # Upload sample data
    csv_path = test_data_dir / "sample.csv"
    with open(csv_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("sample.csv", f, "text/csv")}
        )

    upload_result = assert_response_success(response)
    file_id = upload_result["file_id"]

    # Import data into project
    import_response = client.post(
        f"/api/projects/{project_id}/import/{file_id}"
    )
    assert_response_success(import_response)

    # Query for specific message ID
    query_params = {
        "message_id": 100,
        "start_time": "2024-03-17 10:00:00",
        "end_time": "2024-03-17 10:00:02"
    }

    query_response = client.get(
        f"/api/projects/{project_id}/data",
        params=query_params
    )
    query_result = assert_response_success(query_response)

    assert "data" in query_result
    assert len(query_result["data"]) > 0


@pytest.mark.integration
def test_error_handling(client, test_data_dir):
    """
    Test error handling for various edge cases
    """
    # Test non-existent file
    response = client.get("/api/files/999999")
    assert response.status_code == 404

    # Test invalid file upload
    response = client.post(
        "/api/files/upload",
        files={"file": ("invalid.xyz", b"invalid content", "application/octet-stream")}
    )
    # Should either fail or be accepted as unknown format

    # Test invalid project ID
    response = client.get("/api/projects/999999")
    assert response.status_code == 404


@pytest.mark.integration
def test_performance_large_file(client, test_data_dir):
    """
    Test performance with larger data files
    """
    from utils import create_sample_csv, measure_execution_time

    # Create larger test file
    large_csv_path = test_data_dir / "large_sample.csv"
    create_sample_csv(large_csv_path, num_rows=1000)

    # Upload and measure
    def upload_file():
        with open(large_csv_path, "rb") as f:
            response = client.post(
                "/api/files/upload",
                files={"file": ("large_sample.csv", f, "text/csv")}
            )
        return response

    result, exec_time = measure_execution_time(upload_file)

    upload_result = assert_response_success(result)
    assert "file_id" in upload_result

    # Verify performance is reasonable (should complete in < 5 seconds)
    assert exec_time < 5000, f"Upload took too long: {exec_time}ms"

    # Cleanup
    large_csv_path.unlink()


@pytest.mark.integration
def test_concurrent_operations(client, test_data_dir):
    """
    Test system behavior under concurrent operations
    """
    import concurrent.futures

    csv_path = test_data_dir / "sample.csv"

    def upload_file(index):
        with open(csv_path, "rb") as f:
            response = client.post(
                "/api/files/upload",
                files={"file": (f"concurrent_{index}.csv", f, "text/csv")}
            )
        return response.status_code

    # Upload 5 files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_file, i) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All uploads should succeed
    assert all(status == 200 for status in results)


@pytest.mark.integration
def test_database_cleanup(client, test_data_dir, sample_project):
    """
    Test that database cleanup works correctly
    """
    project_id = sample_project["id"]

    # Upload file
    csv_path = test_data_dir / "sample.csv"
    with open(csv_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("sample.csv", f, "text/csv")}
        )

    upload_result = assert_response_success(response)
    file_id = upload_result["file_id"]

    # Delete project
    delete_response = client.delete(f"/api/projects/{project_id}")
    assert delete_response.status_code == 200

    # Verify project is deleted
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 404

    # Verify file might still exist (depends on implementation)


@pytest.mark.integration
@pytest.mark.dbc
def test_dbc_signal_decoding(client, test_data_dir):
    """
    Test decoding of CAN signals using DBC definition
    """
    # Upload DBC
    dbc_path = test_data_dir / "sample.dbc"
    with open(dbc_path, "rb") as f:
        dbc_response = client.post(
            "/api/files/upload",
            files={"file": ("sample.dbc", f, "text/plain")}
        )

    dbc_result = assert_response_success(dbc_response)
    dbc_file_id = dbc_result["file_id"]

    # Upload log
    log_path = test_data_dir / "sample.log"
    with open(log_path, "rb") as f:
        log_response = client.post(
            "/api/files/upload",
            files={"file": ("sample.log", f, "text/plain")}
        )

    log_result = assert_response_success(log_response)
    log_file_id = log_result["file_id"]

    # Decode signals
    decode_response = client.post(
        "/api/can/decode",
        json={
            "dbc_file_id": dbc_file_id,
            "log_file_id": log_file_id
        }
    )

    decode_result = assert_response_success(decode_response)
    assert "decoded_signals" in decode_result
    assert len(decode_result["decoded_signals"]) > 0

    # Verify known signal exists
    signals = decode_result["decoded_signals"]
    vcu_state_found = any(s["signal_name"] == "VCU_State" for s in signals)
    assert vcu_state_found, "VCU_State signal not found in decoded output"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
