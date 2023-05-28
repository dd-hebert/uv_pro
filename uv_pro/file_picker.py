"""Simple utilities to pick and view files and directories from the console."""
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

    def __init__(self, root):
        """
        Create a FilePicker object.

        Parameters
        ----------
        root : string
            A file path to a directory containing .KD files.

        Returns
        -------
        None.

        """
        self.file_list = []
        self.root = root

        # Get names of subfolders containing .KD files
        # in the :attr:`~FilePicker.root` directory.
        for path, subdirs, _ in os.walk(self.root):
            for name in subdirs:
                # Each folder gets stored as a tuple.
                # The 1st value is the folder name.
                # The 2nd value is a list of .KD files.
                self.file_list.append((name, []))
                for file in os.listdir(os.path.join(path, name)):
                    if file.endswith('.KD'):
                        self.file_list[-1][1].append(file)
                # Pop if folder contains no .KD files
                if self.file_list[-1][1] == []:
                    self.file_list.pop(-1)

        # Handle files directly in the root directory (no subfolder).
        self.file_list.append((self.root, []))
        for file in os.listdir(self.root):
            if file.endswith('.KD'):
                self.file_list[-1][1].append(file)
        # Pop if no .KD files direcly in the root directory
        if self.file_list[-1][1] == []:
            self.file_list.pop(-1)

    def pick_file(self):
        """
        Pick a file interactively from the console to open in view only mode.

        Returns
        -------
        file_path : string
            The path to the chosen file (relative to the ``root directory``).

        """
        # Print list of folders in root directory
        quit_func = False
        print(f'\n{self.root}')
        for index, entry in enumerate(self.file_list):
            if index < len(self.file_list) - 1:
                print(f'[{index + 1}]\t{entry[0]}')
            else:
                print(f'[{index + 1}]\t{entry[0]}')

        # Get user folder choice
        user_folder = input('\nSelect a folder: ')
        while user_folder.isnumeric() is False or int(user_folder) > len(self.file_list):
            if user_folder in ['q', 'Q']:
                quit_func = True
                break
            print('\nInvalid selection. Input a folder number (shown in brackets).')
            user_folder = input("\nSelect a folder or 'q' to quit: ")

        if quit_func is False:
            folder_index = int(user_folder) - 1
            folder_name = self.file_list[folder_index][0]

            # Print list of files in user selected folder
            print(f'\n\t    {folder_name}:')
            for index, file in enumerate(self.file_list[folder_index][1]):
                if index < len(self.file_list[folder_index][1]) - 1:
                    print(f'[{index + 1}]\t    ├───{file}\t')
                else:
                    print(f'[{index + 1}]\t    └───{file}\t')

            # Get user file choice
            user_file = input('\nSelect a file: ')
            while user_file.isnumeric() is False or int(user_file) > len(self.file_list[folder_index][1]):
                if user_file in ['q', 'Q']:
                    quit_func = True
                    break
                print('\nInvalid selection. Input a file number (shown in brackets).')
                user_file = input("\nSelect a file or 'q' to quit: ")

            if quit_func is False:
                file_index = int(user_file) - 1
                file_name = self.file_list[folder_index][1][file_index]

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
