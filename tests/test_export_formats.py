import pytest

from polyzone.io.export_formats import export_to_coco, export_to_yolo


def test_export_to_yolo_normalises_coordinates():
    points = [(10, 20), (30, 40)]
    result = export_to_yolo(points, width=100, height=200)
    assert result == [0.1, 0.1, 0.3, 0.2]


def test_export_to_yolo_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        export_to_yolo([(1, 2)], width=0, height=10)


def test_export_to_coco_flattens_points():
    points = [(1, 2), (3, 4), (5.5, 6.6)]
    result = export_to_coco(points)
    assert result == [1.0, 2.0, 3.0, 4.0, 5.5, 6.6]
