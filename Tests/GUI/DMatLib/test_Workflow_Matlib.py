import sys
from os.path import isdir, isfile, join
from shutil import copytree, rmtree

import mock
from PySide2 import QtWidgets
from pyleecan.Functions.load import LIB_KEY, MACH_KEY, load, load_matlib
from pyleecan.GUI.Dialog.DMachineSetup.DMachineSetup import DMachineSetup
from pyleecan.GUI.Dialog.DMatLib.DMatLib import DMatLib

from Tests import TEST_DATA_DIR
from Tests import save_gui_path as save_path

WS_path = join(save_path, "DMatlib_Workspace_test")
Ref_path = join(TEST_DATA_DIR, "Material", "Workflow")


class TestDMatlibWF(object):
    """Check that the GUI enables to set/modified/add/delete material from the
    Material library and the machine.
    The test machine / library has the following characteristics:
    - stator.mat_type, rotor.mat_type, shaft.mat_type == M400-50A same as matlib
    - rotor.hole[0] = Air missing from Reference library
    - rotor.hole[0].magnet_0.mat_type is an altered version of MagnetPrius
    - rotor.hole[0].magnet_1.mat_type matches MagnetPrius from Library
    """

    def setup_method(self):
        """Setup the workspace and the GUI"""

        # Setup workspace with machine and material copy
        if isdir(WS_path):
            rmtree(WS_path)
        copytree(Ref_path, WS_path)

        # Load Machine
        Toyota_Prius = load(join(WS_path, "Toyota_Prius.json"))
        assert Toyota_Prius.rotor.hole[0].magnet_0.mat_type.name == "MagnetPrius"
        # Load Material Library
        material_dict = load_matlib(machine=Toyota_Prius, matlib_path=WS_path)

        # Machine Setup Widget
        self.widget = DMachineSetup(material_dict=material_dict, machine=Toyota_Prius)

    @classmethod
    def setup_class(cls):
        """Start the app for the test"""
        print("\nStart Test TestDMatlibWF")
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()

    @classmethod
    def teardown_class(cls):
        """Exit the app after the test"""
        if isdir(WS_path):
            rmtree(WS_path)
        cls.app.quit()

    def test_init(self):
        """Test that Machine GUI and WMatSelect are correctly loaded"""
        # Check content of MatLib
        assert self.widget.material_dict is not None
        mat_dict = self.widget.material_dict
        assert LIB_KEY in mat_dict
        assert [mat.name for mat in mat_dict[LIB_KEY]] == [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
        ]
        assert MACH_KEY in mat_dict
        assert [mat.name for mat in mat_dict[MACH_KEY]] == ["Air", "MagnetPrius_old"]
        # Check that all the WMatSelect widget are correctly defined
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
            "Air",
            "MagnetPrius_old",
        ]
        self.widget.nav_step.setCurrentRow(1)  # MachineDimension
        combo = self.widget.w_step.w_mat_0.c_mat_type
        assert combo.currentText() == "M400-50A"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        combo = self.widget.w_step.w_mat.c_mat_type
        assert combo.currentText() == "M400-50A"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        self.widget.nav_step.setCurrentRow(5)  # Winding conductor
        combo = self.widget.w_step.w_mat_0.c_mat_type
        assert combo.currentText() == "Copper1"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        combo = self.widget.w_step.w_mat_1.c_mat_type
        assert combo.currentText() == "Insulator1"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        self.widget.nav_step.setCurrentRow(6)  # LamParam Rotor
        combo = self.widget.w_step.w_mat.c_mat_type
        assert combo.currentText() == "M400-50A"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        self.widget.nav_step.setCurrentRow(7)  # Hole material
        # Mat_void
        combo = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_0.c_mat_type
        assert combo.currentText() == "Air"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        # Magnet_0
        combo = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_1.c_mat_type
        assert (
            self.widget.machine.rotor.hole[0].magnet_0.mat_type.name
            == "MagnetPrius_old"
        )
        assert combo.currentText() == "MagnetPrius_old"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        # Magnet_1
        combo = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_2.c_mat_type
        assert combo.currentText() == "MagnetPrius"
        assert self.widget.machine.rotor.hole[0].magnet_1.mat_type.name == "MagnetPrius"
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items

    def test_edit_matlib(self):
        """Edit a material in the Library and check changes in machine"""
        # Check initial state
        assert self.widget.machine.stator.mat_type.elec.rho == 1
        assert self.widget.machine.rotor.mat_type.elec.rho == 1
        assert self.widget.machine.shaft.mat_type.elec.rho == 1
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 1
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        assert self.widget.w_step.w_mat.current_dialog is None
        self.widget.w_step.w_mat.b_matlib.clicked.emit()
        assert isinstance(self.widget.w_step.w_mat.current_dialog, DMatLib)
        dialog = self.widget.w_step.w_mat.current_dialog
        assert dialog.is_lib_mat is True
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.out_rho_elec.text() == "rho = 1 [ohm.m]"
        # Edit M400-50A material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.lf_rho_elec.setValue(2)
        dialog.current_dialog.lf_rho_elec.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.out_rho_elec.text() == "rho = 2 [ohm.m]"
        assert self.widget.machine.stator.mat_type.elec.rho == 2
        assert self.widget.machine.rotor.mat_type.elec.rho == 2
        assert self.widget.machine.shaft.mat_type.elec.rho == 2
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 2

    def test_edit_machine_material(self):
        """Edit a material from the machine"""
        # Check initial state
        assert self.widget.machine.rotor.hole[0].mat_void.struct.rho == 1.2044
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(7)  # Hole material
        w_mat = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_0
        assert w_mat.current_dialog is None
        w_mat.b_matlib.clicked.emit()
        assert isinstance(w_mat.current_dialog, DMatLib)
        dialog = w_mat.current_dialog
        assert dialog.is_lib_mat is False
        assert dialog.nav_mat_mach.currentRow() == 0
        assert dialog.out_rho_meca.text() == "rho = 1.2044 [kg/m^3]"
        # Edit M400-50A material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.lf_rho_meca.setValue(2.468)
        dialog.current_dialog.lf_rho_meca.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat_mach.currentRow() == 0
        assert dialog.out_rho_meca.text() == "rho = 2.468 [kg/m^3]"
        assert self.widget.machine.rotor.hole[0].mat_void.struct.rho == 2.468

    def test_edit_machine_material_several(self):
        """Edit a material from the machine with several "old" material"""
        # Change M400-50A as old material
        machine = self.widget.machine.copy()
        machine.stator.mat_type.elec.rho = 12
        machine.rotor.mat_type.elec.rho = 12
        machine.shaft.mat_type.elec.rho = 12
        material_dict = load_matlib(machine=machine, matlib_path=WS_path)
        self.widget = DMachineSetup(material_dict=material_dict, machine=machine)
        # Check initial state
        assert self.widget.machine.stator.mat_type.name == "M400-50A_old"
        assert self.widget.machine.rotor.mat_type.name == "M400-50A_old"
        assert self.widget.machine.shaft.mat_type.name == "M400-50A_old"
        assert self.widget.machine.stator.mat_type.elec.rho == 12
        assert self.widget.machine.rotor.mat_type.elec.rho == 12
        assert self.widget.machine.shaft.mat_type.elec.rho == 12
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        assert self.widget.w_step.w_mat.current_dialog is None
        self.widget.w_step.w_mat.b_matlib.clicked.emit()
        assert isinstance(self.widget.w_step.w_mat.current_dialog, DMatLib)
        dialog = self.widget.w_step.w_mat.current_dialog
        assert dialog.is_lib_mat is False
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 3
        assert dialog.nav_mat_mach.currentRow() == 0
        assert dialog.out_rho_elec.text() == "rho = 12 [ohm.m]"
        # Edit M400-50A_old material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.lf_rho_elec.setValue(34)
        dialog.current_dialog.lf_rho_elec.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat_mach.currentRow() == 0
        assert dialog.out_rho_elec.text() == "rho = 34 [ohm.m]"
        assert self.widget.machine.stator.mat_type.elec.rho == 34
        assert self.widget.machine.rotor.mat_type.elec.rho == 34
        assert self.widget.machine.shaft.mat_type.elec.rho == 34

    def test_new_matlib(self):
        """Create a new material in the Library and check changes in the GUI"""
        # Check initial state
        assert self.widget.machine.stator.mat_type.elec.rho == 1
        assert self.widget.machine.rotor.mat_type.elec.rho == 1
        assert self.widget.machine.shaft.mat_type.elec.rho == 1
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 1
        assert not isfile(join(WS_path, "M400-50A_copy.json"))
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        assert self.widget.w_step.w_mat.current_dialog is None
        self.widget.w_step.w_mat.b_matlib.clicked.emit()
        assert isinstance(self.widget.w_step.w_mat.current_dialog, DMatLib)
        dialog = self.widget.w_step.w_mat.current_dialog
        assert dialog.is_lib_mat is True
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 2
        assert dialog.out_name.text() == "name: M400-50A"
        # Copy M400-50A material
        dialog.b_duplicate.clicked.emit()
        assert dialog.current_dialog.le_name.text() == "M400-50A_copy"
        dialog.current_dialog.lf_rho_elec.setValue(2)
        dialog.current_dialog.lf_rho_elec.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat.count() == 5
        assert dialog.nav_mat_mach.count() == 2
        assert dialog.nav_mat.currentRow() == 4
        assert dialog.out_name.text() == "name: M400-50A_copy"
        assert isfile(join(WS_path, "M400-50A_copy.json"))
        combo = self.widget.w_step.w_mat.c_mat_type
        assert combo.currentText() == "M400-50A"
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
            "M400-50A_copy",
            "Air",
            "MagnetPrius_old",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        assert self.widget.machine.stator.mat_type.elec.rho == 1
        assert self.widget.machine.rotor.mat_type.elec.rho == 1
        assert self.widget.machine.shaft.mat_type.elec.rho == 1
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 1
        M400_copy = load(join(WS_path, "M400-50A_copy.json"))
        assert M400_copy.elec.rho == 2

    def test_new_machine_material(self):
        """Create a new material for the machine and check changes in the GUI"""
        # Check initial state
        assert self.widget.machine.rotor.hole[0].magnet_0.mat_type.struct.rho == 7500
        assert not isfile(join(WS_path, "MagnetPrius_old.json"))
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(7)  # Hole material
        w_mat = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_1
        assert w_mat.current_dialog is None
        w_mat.b_matlib.clicked.emit()
        assert isinstance(w_mat.current_dialog, DMatLib)
        dialog = w_mat.current_dialog
        assert dialog.is_lib_mat is False
        assert dialog.nav_mat_mach.currentRow() == 1
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 2
        assert dialog.out_name.text() == "name: MagnetPrius_old"
        # Copy MagnetPrius_old material
        dialog.b_duplicate.clicked.emit()
        assert dialog.current_dialog.le_name.text() == "MagnetPrius_old_copy"
        dialog.current_dialog.lf_rho_meca.setValue(3750)
        dialog.current_dialog.lf_rho_meca.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 3
        assert dialog.nav_mat_mach.currentRow() == 2
        assert dialog.out_name.text() == "name: MagnetPrius_old_copy"
        assert not isfile(join(WS_path, "MagnetPrius_old_copy.json"))
        combo = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_1.c_mat_type
        assert combo.currentText() == "MagnetPrius_old"
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
            "Air",
            "MagnetPrius_old",
            "MagnetPrius_old_copy",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items
        assert self.widget.machine.rotor.hole[0].magnet_0.mat_type.struct.rho == 7500
        assert self.widget.material_dict[MACH_KEY][1].struct.rho == 7500
        assert self.widget.material_dict[MACH_KEY][2].struct.rho == 3750

    def test_rename_matlib(self):
        """rename a material in the Library and check changes in machine"""
        # Check initial state
        assert self.widget.machine.stator.mat_type.elec.rho == 1
        assert self.widget.machine.rotor.mat_type.elec.rho == 1
        assert self.widget.machine.shaft.mat_type.elec.rho == 1
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 1
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        assert self.widget.w_step.w_mat.current_dialog is None
        self.widget.w_step.w_mat.b_matlib.clicked.emit()
        assert isinstance(self.widget.w_step.w_mat.current_dialog, DMatLib)
        dialog = self.widget.w_step.w_mat.current_dialog
        assert dialog.is_lib_mat is True
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.out_rho_elec.text() == "rho = 1 [ohm.m]"
        assert dialog.out_name.text() == "name: M400-50A"
        # Edit M400-50A material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.le_name.setText("M400-50A_V2")
        dialog.current_dialog.le_name.editingFinished.emit()
        dialog.current_dialog.lf_rho_elec.setValue(2)
        dialog.current_dialog.lf_rho_elec.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.nav_mat.item(2).text() == "003 - M400-50A_V2"
        assert dialog.out_rho_elec.text() == "rho = 2 [ohm.m]"
        assert dialog.out_name.text() == "name: M400-50A_V2"
        assert self.widget.machine.stator.mat_type.name == "M400-50A_V2"
        assert self.widget.machine.rotor.mat_type.name == "M400-50A_V2"
        assert self.widget.machine.shaft.mat_type.name == "M400-50A_V2"
        assert self.widget.machine.stator.mat_type.elec.rho == 2
        assert self.widget.machine.rotor.mat_type.elec.rho == 2
        assert self.widget.machine.shaft.mat_type.elec.rho == 2
        assert not isfile(join(WS_path, "M400-50A.json"))
        M4002 = load(join(WS_path, "M400-50A_V2.json"))
        assert M4002.elec.rho == 2
        combo = self.widget.w_step.w_mat.c_mat_type
        assert combo.currentText() == "M400-50A_V2"
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A_V2",
            "MagnetPrius",
            "Air",
            "MagnetPrius_old",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items

    def test_rename_machine_material(self):
        """rename a material in the machine and check changes in machine"""
        # Check initial state
        assert self.widget.machine.rotor.hole[0].mat_void.struct.rho == 1.2044
        assert self.widget.machine.rotor.hole[0].mat_void.name == "Air"
        assert not isfile(join(WS_path, "Air.json"))
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(7)  # Hole material
        w_mat = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_0
        assert w_mat.current_dialog is None
        w_mat.b_matlib.clicked.emit()
        assert isinstance(w_mat.current_dialog, DMatLib)
        dialog = w_mat.current_dialog
        assert dialog.is_lib_mat is False
        assert dialog.nav_mat_mach.currentRow() == 0
        assert dialog.out_rho_meca.text() == "rho = 1.2044 [kg/m^3]"
        assert dialog.out_name.text() == "name: Air"
        # Rename Air material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.le_name.setText("Air-V2")
        dialog.current_dialog.le_name.editingFinished.emit()
        dialog.current_dialog.lf_rho_meca.setValue(2.468)
        dialog.current_dialog.lf_rho_meca.editingFinished.emit()
        dialog.current_dialog.b_save.clicked.emit()
        # Check modifications
        assert dialog.nav_mat_mach.currentRow() == 0
        assert dialog.nav_mat_mach.item(0).text() == "005 - Air-V2"
        assert dialog.out_rho_meca.text() == "rho = 2.468 [kg/m^3]"
        assert dialog.out_name.text() == "name: Air-V2"
        assert self.widget.machine.rotor.hole[0].mat_void.struct.rho == 2.468
        assert self.widget.machine.rotor.hole[0].mat_void.name == "Air-V2"
        assert not isfile(join(WS_path, "Air.json"))
        assert not isfile(join(WS_path, "Air-V2.json"))
        combo = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_0.c_mat_type
        assert combo.currentText() == "Air-V2"
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
            "Air-V2",
            "MagnetPrius_old",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items

    def test_delete_matlib(self):
        """Check that you can delete a material from the material library"""
        # Check initial state
        assert isfile(join(WS_path, "M400-50A.json"))
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        assert self.widget.w_step.w_mat.current_dialog is None
        self.widget.w_step.w_mat.b_matlib.clicked.emit()
        assert isinstance(self.widget.w_step.w_mat.current_dialog, DMatLib)
        dialog = self.widget.w_step.w_mat.current_dialog
        assert dialog.is_lib_mat is True
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 2
        assert dialog.out_name.text() == "name: M400-50A"
        # Delete M400-50A material
        with mock.patch(
            "PySide2.QtWidgets.QMessageBox.question",
            return_value=QtWidgets.QMessageBox.Yes,
        ):
            dialog.b_delete.clicked.emit()
        # Check modifications
        assert dialog.nav_mat.count() == 3
        assert dialog.nav_mat_mach.count() == 3  # M400-50A is now a machine mat
        assert dialog.nav_mat.currentRow() == 0
        assert dialog.out_name.text() == "name: Copper1"
        assert not isfile(join(WS_path, "M400-50A.json"))
        combo = self.widget.w_step.w_mat.c_mat_type
        assert combo.currentText() == "M400-50A"
        exp_items = [
            "Copper1",
            "Insulator1",
            "MagnetPrius",
            "M400-50A",
            "Air",
            "MagnetPrius_old",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items

    def test_edit_matlib_to_machine(self):
        """Edit a material in the Library and save it in the machine"""
        # Check initial state
        assert self.widget.machine.stator.mat_type.elec.rho == 1
        assert self.widget.machine.rotor.mat_type.elec.rho == 1
        assert self.widget.machine.shaft.mat_type.elec.rho == 1
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 1
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(2)  # LamParam Stator
        assert self.widget.w_step.w_mat.current_dialog is None
        self.widget.w_step.w_mat.b_matlib.clicked.emit()
        assert isinstance(self.widget.w_step.w_mat.current_dialog, DMatLib)
        dialog = self.widget.w_step.w_mat.current_dialog
        assert dialog.is_lib_mat is True
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 2
        assert dialog.nav_mat.currentRow() == 2
        assert dialog.out_rho_elec.text() == "rho = 1 [ohm.m]"
        # Edit M400-50A material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.lf_rho_elec.setValue(2)
        dialog.current_dialog.lf_rho_elec.editingFinished.emit()
        dialog.current_dialog.b_add_matlib.clicked.emit()
        # Check modifications
        assert not dialog.is_lib_mat
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 3
        assert dialog.nav_mat_mach.currentRow() == 2
        assert dialog.nav_mat_mach.item(2).text() == "007 - M400-50A_edit"
        assert dialog.out_name.text() == "name: M400-50A_edit"
        assert dialog.out_rho_elec.text() == "rho = 2 [ohm.m]"
        assert self.widget.machine.stator.mat_type.name == "M400-50A_edit"
        assert self.widget.machine.rotor.mat_type.name == "M400-50A_edit"
        assert self.widget.machine.shaft.mat_type.name == "M400-50A_edit"
        assert self.widget.machine.stator.mat_type.elec.rho == 2
        assert self.widget.machine.rotor.mat_type.elec.rho == 2
        assert self.widget.machine.shaft.mat_type.elec.rho == 2
        M400 = load(join(WS_path, "M400-50A.json"))
        assert M400.elec.rho == 1
        assert self.widget.material_dict[LIB_KEY][2].name == "M400-50A"
        assert self.widget.material_dict[LIB_KEY][2].elec.rho == 1
        assert not isfile(join(WS_path, "M400-50A_edit.json"))
        combo = self.widget.w_step.w_mat.c_mat_type
        assert combo.currentText() == "M400-50A_edit"
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
            "Air",
            "MagnetPrius_old",
            "M400-50A_edit",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items

    def test_edit_machine_to_library(self):
        """Edit a material from the machine to the library"""
        # Check initial state
        assert (
            self.widget.machine.rotor.hole[0].magnet_0.mat_type.name
            == "MagnetPrius_old"
        )
        assert self.widget.machine.rotor.hole[0].magnet_0.mat_type.struct.rho == 7500
        assert not isfile(join(WS_path, "MagnetPrius_old.json"))
        assert not isfile(join(WS_path, "MagnetPriusV1.json"))
        # Open DMatlib
        self.widget.nav_step.setCurrentRow(7)  # Hole material
        w_mat = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_1
        assert w_mat.current_dialog is None
        w_mat.b_matlib.clicked.emit()
        assert isinstance(w_mat.current_dialog, DMatLib)
        dialog = w_mat.current_dialog
        assert dialog.is_lib_mat is False
        assert dialog.nav_mat.count() == 4
        assert dialog.nav_mat_mach.count() == 2
        assert dialog.nav_mat_mach.currentRow() == 1
        assert dialog.out_name.text() == "name: MagnetPrius_old"
        assert dialog.out_rho_meca.text() == "rho = 7500 [kg/m^3]"
        # Edit M400-50A material
        dialog.b_edit.clicked.emit()
        dialog.current_dialog.le_name.setText("MagnetPriusV1")
        dialog.current_dialog.le_name.editingFinished.emit()
        dialog.current_dialog.lf_rho_meca.setValue(1234)
        dialog.current_dialog.lf_rho_meca.editingFinished.emit()
        dialog.current_dialog.b_add_matlib.clicked.emit()
        # Check modifications
        assert (
            self.widget.machine.rotor.hole[0].magnet_0.mat_type.name == "MagnetPriusV1"
        )
        assert self.widget.machine.rotor.hole[0].magnet_0.mat_type.struct.rho == 1234
        assert dialog.is_lib_mat is True
        assert dialog.nav_mat.count() == 5
        assert dialog.nav_mat_mach.count() == 1
        assert dialog.nav_mat.currentRow() == 4
        assert dialog.out_name.text() == "name: MagnetPriusV1"
        assert dialog.out_rho_meca.text() == "rho = 1234 [kg/m^3]"

        assert isfile(join(WS_path, "MagnetPriusV1.json"))
        Mag = load(join(WS_path, "MagnetPriusV1.json"))
        assert Mag.struct.rho == 1234
        combo = self.widget.w_step.tab_hole.widget(0).w_hole.w_mat_1.c_mat_type
        assert combo.currentText() == "MagnetPriusV1"
        exp_items = [
            "Copper1",
            "Insulator1",
            "M400-50A",
            "MagnetPrius",
            "MagnetPriusV1",
            "Air",
        ]
        assert [combo.itemText(i) for i in range(combo.count())] == exp_items


if __name__ == "__main__":
    a = TestDMatlibWF()
    a.setup_class()
    a.setup_method()
    a.test_delete_matlib()
    print("Done")
