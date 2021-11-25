import os
def delete_file():
    # create list of folder to remove files from
    folders = []

    # For the future
    # folders.append(os.path.dirname(__file__) + r'\add_new_pnts_by_angle\results_file')

    folders.append(os.path.dirname(__file__) + r'\fix_geometry\results_file')
    folders.append(os.path.dirname(__file__) + r'\general')
    folders.append(os.path.dirname(__file__) + r'\mean_close_point\results_file')
    folders.append(os.path.dirname(__file__) + r'\POI\results_file')
    # folders.append(os.path.dirname(os.path.dirname(__file__)) + r'\results')
    for folder in folders:
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)
