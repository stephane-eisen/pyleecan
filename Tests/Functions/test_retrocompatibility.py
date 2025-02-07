# -*- coding: utf-8 -*-


from os.path import isfile, join

import pytest
from numpy import array_equal
from pyleecan.definitions import DATA_DIR
from pyleecan.Functions.load import load
from Tests import TEST_DATA_DIR

# 1: LamSlotMag convertion (magnet from slot to lamination)
mag_list = list()
mag_list.append(
    {
        "ref": join(DATA_DIR, "Machine", "SPMSM_001.json"),
        "old": join(TEST_DATA_DIR, "Retrocompatibility", "Magnet", "SPMSM_001.json"),
    }
)

# 2: Winding convertion (star of slot)
wind_list = list()
# wind_list.append(  # WindingSC + WindingDW2L
#     {
#         "ref": join(DATA_DIR, "Machine", "SCIM_001.json"),
#         "old": join(TEST_DATA_DIR, "Retrocompatibility", "Winding", "SCIM_001.json"),
#     }
# )
wind_list.append(  # WindingCW1L
    {
        "ref": join(DATA_DIR, "Machine", "SPMSM_002.json"),
        "old": join(TEST_DATA_DIR, "Retrocompatibility", "Winding", "SPMSM_002.json"),
    }
)
wind_list.append(  # WindingCW2LT
    {
        "ref": join(DATA_DIR, "Machine", "SPMSM_015.json"),
        "old": join(TEST_DATA_DIR, "Retrocompatibility", "Winding", "SPMSM_015.json"),
    }
)
wind_list.append(  # WindingUD
    {
        "ref": join(DATA_DIR, "Machine", "SPMSM_020.json"),
        "old": join(TEST_DATA_DIR, "Retrocompatibility", "Winding", "SPMSM_020.json"),
    }
)
# wind_list.append(  # WindingSC + WindingDW2L
#     {
#         "ref": join(DATA_DIR, "Machine", "TESLA_S.json"),
#         "old": join(TEST_DATA_DIR, "Retrocompatibility", "Winding", "TESLA_S.json"),
#     }
# )
wind_list.append(  # WindingDW1L
    {
        "ref": join(DATA_DIR, "Machine", "Toyota_Prius.json"),
        "old": join(
            TEST_DATA_DIR, "Retrocompatibility", "Winding", "Toyota_Prius.json"
        ),
    }
)


@pytest.mark.parametrize("file_dict", mag_list)
def test_save_load_mag_retro(file_dict):
    """Check that the LamSlotMag convertion works"""
    ref = load(file_dict["ref"])
    old = load(file_dict["old"])

    # Don't track material update
    ref.rotor.mat_type = None
    ref.rotor.magnet.mat_type = None
    old.rotor.mat_type = None
    old.rotor.magnet.mat_type = None

    # Check old file is converted to current version
    msg = "Error for " + ref.name + ": " + str(ref.rotor.compare(old.rotor, "rotor"))
    assert ref.rotor == old.rotor, msg


@pytest.mark.parametrize("file_dict", wind_list)
def test_save_load_wind_retro(file_dict):
    """Check that the winding convertion works (convert to WindingUD instead of Winding)"""
    ref = load(file_dict["ref"])
    old = load(file_dict["old"])

    # Check old file is converted to current version
    if hasattr(ref.rotor, "winding"):
        msg = (
            "Error for "
            + ref.name
            + ": "
            + str(ref.rotor.winding.compare(old.rotor.winding, "rotor.winding"))
        )
        assert ref.rotor.winding == old.rotor.winding, msg

    msg = "Error for " + ref.name
    assert ref.stator.winding.p == old.stator.winding.p, msg
    assert ref.stator.winding.qs == old.stator.winding.qs, msg
    assert ref.stator.winding.Ntcoil == old.stator.winding.Ntcoil, msg
    assert array_equal(
        ref.stator.winding.get_connection_mat(),
        -1 * old.stator.winding.get_connection_mat(),
    ) or array_equal(
        ref.stator.winding.get_connection_mat(),
        old.stator.winding.get_connection_mat(),
    ), msg


if __name__ == "__main__":
    for file_dict in mag_list:
        test_save_load_mag_retro(file_dict)

    for file_dict in wind_list:
        test_save_load_wind_retro(file_dict)
