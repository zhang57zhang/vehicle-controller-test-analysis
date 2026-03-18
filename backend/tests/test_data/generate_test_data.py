"""
Generate test data files for vehicle controller test analysis system
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_test_data():
    """Create various test data files"""

    # Sample data
    data = {
        'timestamp': ['2024-03-17 10:00:00.000', '2024-03-17 10:00:00.050',
                      '2024-03-17 10:00:00.100', '2024-03-17 10:00:00.150',
                      '2024-03-17 10:00:01.000', '2024-03-17 10:00:01.050',
                      '2024-03-17 10:00:01.100', '2024-03-17 10:00:01.150'],
        'message_id': [100, 200, 300, 400, 100, 200, 300, 400],
        'message_name': ['VCU_Status', 'BMS_Data', 'Motor_Torque', 'MCU_Control',
                         'VCU_Status', 'BMS_Data', 'Motor_Torque', 'MCU_Control'],
        'signal_name': ['VCU_State', 'BMS_SOC', 'Motor_Speed', 'MCU_Torque_Command',
                       'VCU_State', 'BMS_SOC', 'Motor_Speed', 'MCU_Torque_Command'],
        'signal_value': [2.0, 85.0, 1500.0, 150.0, 3.0, 84.8, 2000.0, 200.0],
        'unit': ['', '%', 'rpm', 'Nm', '', '%', 'rpm', 'Nm']
    }

    df = pd.DataFrame(data)

    # Create Excel file
    df.to_excel('sample.xlsx', index=False)
    print("Created sample.xlsx")

    # Create MATLAB v6 format file (requires scipy)
    try:
        from scipy.io import savemat
        mat_data = {
            'timestamp': df['timestamp'].values,
            'message_id': df['message_id'].values,
            'message_name': df['message_name'].values,
            'signal_name': df['signal_name'].values,
            'signal_value': df['signal_value'].values,
            'unit': df['unit'].values
        }
        savemat('sample_v6.mat', mat_data, format='4', do_compression=False)
        print("Created sample_v6.mat")
    except ImportError:
        print("Warning: scipy not available, skipping MATLAB v6 file creation")

    # Create MATLAB v7.3 format file (requires h5py)
    try:
        from scipy.io import savemat
        import h5py
        mat_data = {
            'timestamp': df['timestamp'].values,
            'message_id': df['message_id'].values,
            'message_name': df['message_name'].values,
            'signal_name': df['signal_name'].values,
            'signal_value': df['signal_value'].values,
            'unit': df['unit'].values
        }
        savemat('sample_v73.mat', mat_data, format='7.3', do_compression=True)
        print("Created sample_v73.mat")
    except ImportError:
        print("Warning: h5py or scipy not available, skipping MATLAB v7.3 file creation")

    print("\nAll test data files generated successfully!")

if __name__ == "__main__":
    create_test_data()
