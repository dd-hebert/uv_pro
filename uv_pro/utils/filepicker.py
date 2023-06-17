# -*- coding: utf-8 -*-
"""
Simple utilities to view directories and pick files from the terminal.

@author: David Hebert
"""

import os


class FilePicker:
    """
    A FilePicker object.

    Contains methods to pick and view files and directories from the console.

    Attributes
    ----------
    file_list : list
        A list of tuples containing a subfolder name ``file_list[x][0]`` and
        a list of files in each subfolder ``file_list[x][1]``.

    """

    def __init__(self, root, file_ext):
        """
        Initialize a FilePicker object.

        Parameters
        ----------
        root : string
            A file path to a directory containing folders and files.
        file_ext : string
            The file extension of interest (e.g., '.jpeg').

        Returns
        -------
        None.

        """
        self.root = os.path.abspath(root)
        self.ext = file_ext
        self.file_list = self._build_file_list()

    def _build_file_list(self):
        """
        Build the list of files with the specified extension in the root directory.

        Returns
        -------
        None.

        """
        print(f'Searching "{self.root}" for .KD files...')
        file_list = [
            (
                os.path.relpath(path, self.root),
                [file for file in files if os.path.splitext(file)[1].lower() == self.ext.lower()]
            )
            for path, subdirs, files in os.walk(self.root)]

        file_list = [(folder, files) for folder, files in file_list if files]

        if file_list == []:
            return None

        return file_list

    def pick_file(self):
        """
        Pick a file interactively from the terminal.

        Returns
        -------
        file_path : string
            Returns the path of the chosen file relative to the root directory.

        """
        if self.file_list:
            while True:
                self._print_folders_in_root()
                folder_choice = self._get_folder_choice()

                if folder_choice is None:
                    return None  # User wants to quit

                folder_index, folder_name = folder_choice
                self._print_files_in_folder(folder_index, folder_name)
                file_choice = self._get_file_choice(folder_index, folder_name)

                if file_choice is None:
                    return None  # User wants to quit
                elif file_choice == 'back':
                    continue  # Go back to folder selection
                else:
                    return self._print_selection(folder_name, file_choice)

    def _print_folders_in_root(self):
        # Print list of folders in root directory
        print(f'\n{self.root}')
        max_digits = len(str(len(self.file_list)))
        for index, entry in enumerate(self.file_list):
            extra_spacing = max_digits - len(str(index + 1))
            spacing = ' ' * (4 + extra_spacing)
            print(f'[{index + 1}]{spacing}{entry[0]}')

    def _get_folder_choice(self):
        # Get user folder choice
        user_folder = input('\nSelect a folder: ')
        accepted_range = range(1, len(self.file_list) + 1)

        if user_folder in ['q', 'Q']:
            return None
        elif user_folder.isnumeric() is False or int(user_folder) not in accepted_range:
            self._print_folders_in_root()
            print('\nInvalid selection. Input a folder number (shown in brackets)',
                  'or q to quit.')
            return self._get_folder_choice()
        else:
            folder_index = int(user_folder) - 1
            folder_name = self.file_list[folder_index][0]

            return folder_index, folder_name

    def _print_files_in_folder(self, folder_index, folder_name):
        # Print list of files in user selected folder
        max_digits = len(str(len(self.file_list[folder_index][1])))
        spacing = ' ' * (6 + max_digits)
        print(f'\n{spacing}{folder_name}:')
        for index, file in enumerate(self.file_list[folder_index][1]):
            extra_spacing = max_digits - len(str(index + 1))
            spacing = ' ' * (4 + extra_spacing)
            if index < len(self.file_list[folder_index][1]) - 1:
                print(f'[{index + 1}]{spacing}├───{file}\t')
            else:
                print(f'[{index + 1}]{spacing}└───{file}\t')

    def _get_file_choice(self, folder_index, folder_name):
        # Get user file choice
        user_file = input('\nSelect a file: ')
        accepted_range = range(1, len(self.file_list[folder_index][1]) + 1)

        if user_file in ['q', 'Q']:
            return None
        elif user_file in ['b', 'B']:
            return 'back'  # Indicates going back
        elif user_file.isnumeric() is False or int(user_file) not in accepted_range:
            self._print_files_in_folder(folder_index, folder_name)
            print('\nInvalid selection. Input a file number (shown in brackets)',
                  'or q (quit), b (back).')
            return self._get_file_choice(folder_index, folder_name)
        else:
            file_index = int(user_file) - 1
            file_name = self.file_list[folder_index][1][file_index]

            return file_name

    def _print_selection(self, folder_name, file_name):
        print('┏' + '┅' * (len(file_name) + 17) + '┓')
        print(f'┇ File selected: {file_name} ┇')
        print('┗' + '┅' * (len(file_name) + 17) + '┛')

        # Get file path
        if folder_name == 'root':
            file_path = os.path.join(file_name)
        else:
            file_path = os.path.join(folder_name, file_name)

        return file_path

    def tree(self):
        """
        Print the ``root directory`` file tree to the console.

        Returns
        -------
        None. Prints a file tree.

        """
        print(self.root)
        if self.file_list:
            for index, entry in enumerate(self.file_list):
                if index < len(self.file_list) - 1:
                    print(f'├───{entry[0]}')
                    for i, file in enumerate(entry[1]):
                        if i < len(entry[1]) - 1:
                            print(f'│   ├───{file}\t')
                        else:
                            print(f'│   └───{file}\t')
                else:
                    print(f'└───{entry[0]}')
                    for i, file in enumerate(entry[1]):
                        if i < len(entry[1]) - 1:
                            print(f'    ├───{file}\t')
                        else:
                            print(f'    └───{file}\t')
