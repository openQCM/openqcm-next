def approx_columns(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open("output_file.txt", 'w') as output_file:
        for line in lines:
            # Split the line into columns
            columns = line.strip().split()

            # Check if the line has the expected number of columns
            if len(columns) >= 3:
                # Approximate each column as required
                freq = int(float(columns[0]))
                amp = round(float(columns[1]), 1)
                phase = round(float(columns[2]), 1)

                # Write the approximated values to the output file
                output_file.write(f"{freq} {amp} {phase}\n")
            else:
                # If the line does not have enough columns, write it as is
                output_file.write(line)

# Replace 'path_to_your_file.txt' with the path to your text file
approx_columns('Calibration_5MHz_air_cp.txt')

