# MATLAB Test Data Files

## Overview
This directory contains test data files for the vehicle controller test analysis system.

## Files

### sample_v6.mat (MATLAB v6 format)
This file should contain:
- timestamp: datetime array
- message_id: uint16 array
- message_name: cell array of strings
- signal_name: cell array of strings
- signal_value: double array
- unit: cell array of strings

### sample_v73.mat (MATLAB v7.3 format)
Same structure as v6 but saved in HDF5-based v7.3 format for better performance with large datasets.

## Generation Instructions

Run the following Python script to generate MATLAB files:

```bash
cd backend/tests/test_data
python generate_test_data.py
```

This requires:
- scipy (for both formats)
- h5py (for v7.3 format)

## Sample Data Structure

```matlab
% In MATLAB workspace:
whos
  Name                Size            Bytes  Class      Attributes
  timestamp           8x1                64  datetime
  message_id          8x1                16  uint16
  message_name        8x1               672  cell
  signal_name         8x1               672  cell
  signal_value        8x1                64  double
  unit                8x1               672  cell
```

## Manual Generation (Alternative)

If the Python script is not available, you can create these files manually in MATLAB:

```matlab
% Create sample data
timestamp = datetime(2024,3,17,10,0,0) + seconds(0:7)'*[0;0.05;0.1;0.15;1;1.05;1.1;1.15];
message_id = [100;200;300;400;100;200;300;400];
message_name = {'VCU_Status','BMS_Data','Motor_Torque','MCU_Control','VCU_Status','BMS_Data','Motor_Torque','MCU_Control'}';
signal_name = {'VCU_State','BMS_SOC','Motor_Speed','MCU_Torque_Command','VCU_State','BMS_SOC','Motor_Speed','MCU_Torque_Command'}';
signal_value = [2;85;1500;150;3;84.8;2000;200];
unit = {'','%','rpm','Nm','','%','rpm','Nm'}';

% Save as v6 format
save('sample_v6.mat', '-v6', 'timestamp', 'message_id', 'message_name', 'signal_name', 'signal_value', 'unit')

% Save as v7.3 format
save('sample_v73.mat', '-v7.3', 'timestamp', 'message_id', 'message_name', 'signal_name', 'signal_value', 'unit')
```
