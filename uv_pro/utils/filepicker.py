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
    file_list : list[tuple, ...]
        A list of tuples containing a subfolder name ``file_list[x][0]`` and
        a list of files in each subfolder ``file_list[x][1]``.
    """

    def __init__(self, root: str, file_ext: str) -> None:
        """
        Initialize a FilePicker object.

        Parameters
        ----------
        root : str
            A file path to a directory containing folders and files.
        file_ext : str
            The file extension of interest (e.g., '.jpeg').
        """
        self.root = os.path.abspath(root)
        self.ext = file_ext
        self.file_list = self._build_file_list()

    def _build_file_list(self) -> list:
        """Build the list of files with the specified extension in the root directory."""
        print(f'Searching "{self.root}" for {self.ext} files...')

        file_list = [
            (
                os.path.relpath(path, self.root),
                [file for file in files if os.path.splitext(file)[1].lower() == self.ext.lower()]
            )
            for path, subdirs, files in os.walk(self.root)
        ]

        file_list = [(folder, files) for folder, files in file_list if files]

        if file_list:
            # print(file_list)
            return file_list

        print('No files found.')
        return None

    def pick_file(self, mode: str = 'single', min_files: int = 0, max_files: int = 100) -> list[str] | None:
        """
        Pick files interactively from the terminal.

        Parameters
        ----------
        mode : str
            Specify selection of a single or multiple files. Either \
            'single' or 'multi'. Default is 'single'.

        Returns
        -------
        file_path : list[str] or None
            The path of the chosen file(s) relative to the root directory.
        """
        if not self.file_list:
            return None

        while True:
            if len(self.file_list) > 1:
                self._print_folders_in_root()
                folder_choice = self._get_folder_choice()

                if folder_choice is None:
                    return None

                folder_index, folder_name = folder_choice

            else:  # Directly print files in root
                folder_index, folder_name = (0, self.file_list[0][0])

            self._print_files_in_folder(folder_index, folder_name)

            file_choices = self._get_file_choice(folder_index, folder_name, mode, min_files, max_files)

            if file_choices is None:
                return None

            elif file_choices == ['back']:
                continue

            else:
                self._print_selection(file_choices)
                return [os.path.join(folder_name, file_name) for file_name in file_choices]

    def _print_folders_in_root(self):
        print(f'\n{self.root}')
        max_digits = len(str(len(self.file_list)))

        for index, entry in enumerate(self.file_list):
            extra_spacing = max_digits - len(str(index + 1))
            spacing = ' ' * (4 + extra_spacing)
            print(f'[{index + 1}]{spacing}{entry[0]}')

    def _get_folder_choice(self) -> tuple[int, str] | None:
        try:
            selection = input('\nSelect a folder: ')
            accepted_range = range(1, len(self.file_list) + 1)

        except (EOFError, KeyboardInterrupt):
            return None

        if selection.isnumeric() is False or int(selection) not in accepted_range:
            self._print_folders_in_root()
            print('\nInvalid selection. Input a folder number (shown in brackets)')
            return self._get_folder_choice()

        else:
            folder_index = int(selection) - 1
            folder_name = self.file_list[folder_index][0]
            return folder_index, folder_name

    def _print_files_in_folder(self, folder_index: int, folder_name: str) -> None:
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

    def _get_file_choice(self, folder_index: int, folder_name: str, mode: str = 'single',
                         min_files: int = 1, max_files: int = 100) -> list[str] | None:
        try:
            if mode == 'single':
                prompt = '\nSelect a file: '

            elif mode == 'multi':
                prompt = f'\nSelect multiple {self.ext} files by entering the numbers in brackets separated by spaces: '

            selection = [entry.lower() for entry in set(input(prompt).split())]

        except (EOFError, KeyboardInterrupt):
            return None

        return self._validate_file_choice(selection, folder_index, folder_name, mode, min_files, max_files)

    def _validate_file_choice(self, selection: list[str], folder_index: int, folder_name: str, mode: str, min_files: int, max_files: int) -> list[str]:
        if any((entry in ['b', 'back'] for entry in selection)):
            return ['back']

        accepted_range = range(1, len(self.file_list[folder_index][1]) + 1)

        if any((not entry.isdigit() or int(entry) not in accepted_range for entry in selection)):
            self._print_files_in_folder(folder_index, folder_name)
            message = 'Invalid selection. Input a file number (shown in brackets) or b to go back.'
            print(f'\n{message}')
            return self._get_file_choice(folder_index, folder_name, mode, min_files, max_files)

        if len(selection) < min_files:
            self._print_files_in_folder(folder_index, folder_name)
            message = f'Too few files selected. Select at least {min_files} {self.ext} files.'
            print(f'\n{message}')
            return self._get_file_choice(folder_index, folder_name, mode, min_files, max_files)

        if len(selection) > max_files:
            self._print_files_in_folder(folder_index, folder_name)
            message = f'Too many files selected. Select fewer than {max_files} {self.ext} files.'
            print(f'\n{message}')
            return self._get_file_choice(folder_index, folder_name, mode, min_files, max_files)

        return [self.file_list[folder_index][1][int(entry) - 1] for entry in sorted(selection)]

    def _print_selection(self, file_names: list[str]) -> str:
        max_length = len(max(file_names, key=len)) + 2

        print('┏' + '┅' * max_length + '┓')
        print(f'┇{"File(s) selected:":^{max_length}}┇')

        for file in file_names:
            right_padding = (max_length - len(file)) - 2
            print('┇ ' + file + ' ' * right_padding + ' ┇')

        print('┗' + '┅' * max_length + '┛')

    def tree(self) -> None:
        """Print the root directory file tree to the console."""
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
