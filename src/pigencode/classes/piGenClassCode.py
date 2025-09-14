import os, json
from pathlib import Path
from ..defs.fileIO import getKeyItem, piGCDirs
from ..defs.piJsonFile import readJson
from ..defs.logIt import logIt, printIt, lable

class PiGenClassCode():
    def __init__(self):
        self.testStr = f'self.testStr: {__name__}'
        indent = 4
        self.indent = ' ' * indent
        self.savedCodeFiles = {}

    def __str__(self) -> str:
        return self.testStr

    def __setPiGenClassAttrs(self) -> None:
        """Extract attributes from piGenClass JSON structure"""
        self.piGenClass = self.pi_piGenClass["piBody"]["piGenClass"]

        try: self.headers = self.piGenClass["headers"]
        except: self.headers = []

        try: self.imports = self.piGenClass["imports"]
        except: self.imports = []

        try: self.fromImports = self.piGenClass["fromImports"]
        except: self.fromImports = {}

        try: self.constants = self.piGenClass["constants"]
        except: self.constants = []

        try: self.fileDirectory = self.piGenClass["fileDirectory"]
        except: self.fileDirectory = ""

        try: self.fileName = self.piGenClass["fileName"]
        except: self.fileName = "classes"

        try: self.classDefs = self.piGenClass["classDefs"]
        except: self.classDefs = {}

        try: self.globalCode = self.piGenClass["globalCode"]
        except: self.globalCode = []

    def __buildPiGenClassCode(self) -> str:
        """Build the complete Python class file content"""
        code_lines = []

        # Add headers
        if self.headers:
            for header in self.headers:
                code_lines.append(header)
            code_lines.append("")  # Blank line after headers

        # Handle __future__ imports first (they must come before any other imports)
        future_imports = []
        regular_from_imports = {}
        
        if self.fromImports:
            for module_key, import_info in self.fromImports.items():
                from_module = import_info.get("from", "")
                if from_module == "__future__":
                    future_imports.append(import_info)
                else:
                    regular_from_imports[module_key] = import_info
        
        # Add __future__ imports first
        if future_imports:
            for import_info in future_imports:
                from_module = import_info.get("from", "")
                import_items = import_info.get("import", "")
                if from_module and import_items:
                    code_lines.append(f"from {from_module} import {import_items}")

        # Add regular imports
        if self.imports:
            for imp in self.imports:
                code_lines.append(f"import {imp}")

        # Add remaining from imports
        if regular_from_imports:
            for module_key, import_info in regular_from_imports.items():
                from_module = import_info.get("from", "")
                import_items = import_info.get("import", "")
                if from_module and import_items:
                    code_lines.append(f"from {from_module} import {import_items}")

        # Add blank line after imports if we have imports
        if self.imports or self.fromImports:
            code_lines.append("")

        # Add constants
        if self.constants:
            for constant in self.constants:
                # Unescape quotes that were escaped during syncCode process
                unescaped_constant = constant.replace('\\"', '"')
                code_lines.append(unescaped_constant)
            code_lines.append("")  # Blank line after constants

        # Add class definitions
        if self.classDefs:
            class_names = list(self.classDefs.keys())
            for i, class_name in enumerate(class_names):
                class_code = self.classDefs[class_name]

                # Add class code lines
                for line in class_code:
                    # Unescape quotes that were escaped during syncCode process
                    unescaped_line = line.replace('\\"', '"')
                    code_lines.append(unescaped_line)

                # Add blank line between classes (except after the last one)
                if i < len(class_names) - 1:
                    code_lines.append("")

        # Add global code at the end
        if self.globalCode:
            if self.classDefs:  # Add blank line before global code if we have classes
                code_lines.append("")
            for line in self.globalCode:
                # Unescape quotes that were escaped during syncCode process
                unescaped_line = line.replace('\\"', '"')
                code_lines.append(unescaped_line)

        return '\n'.join(code_lines)

    def __getFileDirectory(self) -> Path:
        """Get the target directory for the generated file"""
        if self.fileDirectory:
            # Use specified directory
            target_dir = Path(self.fileDirectory)
        else:
            # Use RC configuration or default
            target_dir = Path(getKeyItem(piGCDirs[4]))

        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def __saveTrackingFile(self, target_dir: Path, filename: str):
        """Save tracking file for rmGC cleanup"""
        tracking_file = target_dir / ".piclass"

        try:
            # Read existing tracking data
            tracking_data = []
            if tracking_file.exists():
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    tracking_data = [line.strip() for line in f.readlines()]

            # Add this file if not already tracked
            if filename not in tracking_data:
                tracking_data.append(filename)

            # Write updated tracking data
            with open(tracking_file, 'w', encoding='utf-8') as f:
                for tracked_file in tracking_data:
                    f.write(f"{tracked_file}\n")

        except Exception as e:
            printIt(f"Warning: Could not update tracking file: {e}", lable.WARN)

    def genPiGenClass(self, piGenClassFile: str) -> str:
        """
            Generate Python class file from piGenClass JSON
            Returns resulting file name
        """
        try:
            # Read the piGenClass JSON file
            self.pi_piGenClass = readJson(piGenClassFile)
            if not self.pi_piGenClass:
                printIt(f"Failed to read piGenClass file: {piGenClassFile}", lable.ERROR)
                return ""

            # Extract attributes
            self.__setPiGenClassAttrs()

            # Build the Python code
            python_code = self.__buildPiGenClassCode()

            # Determine output file path
            target_dir = self.__getFileDirectory()
            output_filename = f"{self.fileName}.py"
            output_path = target_dir / output_filename

            # Write the Python file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(python_code)

            # Save tracking file for rmGC
            self.__saveTrackingFile(target_dir, output_filename)

            # Record in saved files
            self.savedCodeFiles[output_path] = str(output_path)

            return str(output_path)

        except Exception as e:
            printIt(f"Error generating piGenClass file: {e}", lable.ERROR)
            return ""

def genPiGenClass(piGenClassFile: str) -> str:
    """Generate Python class file from piGenClass JSON file"""
    generator = PiGenClassCode()
    return generator.genPiGenClass(piGenClassFile)
