import os
import os
import io
import pytest
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage

from src import file_utils
from src.config import Config

def test_allowed_file(monkeypatch):
    monkeypatch.setattr(file_utils.config, 'ALLOWED_EXTENSIONS', {'txt', 'jpg'})
    assert file_utils.allowed_file('test.txt') is True
    assert file_utils.allowed_file('image.jpg') is True
    assert file_utils.allowed_file('document.pdf') is False
    assert file_utils.allowed_file('no_extension') is False

def test_get_file_size():
    mock_file = MagicMock()
    mock_file.tell.return_value = 1024
    size = file_utils.get_file_size(mock_file)
    assert size == 1024
    mock_file.seek.assert_any_call(0, 2)
    mock_file.seek.assert_any_call(0)

def test_save_uploaded_file(tmp_path):
    mock_file = FileStorage(
        stream=io.BytesIO(b'test content'),
        filename='test_upload.txt',
        content_type='text/plain'
    )
    
    filepath, filename = file_utils.save_uploaded_file(mock_file, str(tmp_path))
    
    assert filename == 'test_upload.txt'
    assert os.path.exists(filepath)
    assert os.path.basename(filepath) == 'test_upload.txt'
    with open(filepath, 'rb') as f:
        assert f.read() == b'test content'

def test_clean_processed_folder(monkeypatch, tmp_path):
    processed_dir = tmp_path / 'processed'
    processed_dir.mkdir()

    monkeypatch.setattr(file_utils.config, 'PROCESSED_FOLDER', str(processed_dir))
    monkeypatch.setattr(file_utils.config, 'MAX_PROCESSED_FILES', 2)
    monkeypatch.setattr(os, 'getcwd', lambda: str(tmp_path))

    # Create some dummy files with different modification times
    files_to_create = ['file1.txt', 'file2.txt', 'file3.txt', 'file4.txt']
    for i, filename in enumerate(files_to_create):
        filepath = processed_dir / filename
        filepath.touch()
        # manually set modification time
        os.utime(filepath, (i, i))

    file_utils.clean_processed_folder()

    remaining_files = os.listdir(processed_dir)
    assert len(remaining_files) == 2
    assert 'file3.txt' in remaining_files
    assert 'file4.txt' in remaining_files

def test_move_processed_files(monkeypatch, tmp_path):
    project_root = tmp_path
    processed_dir = project_root / 'processed'
    processed_dir.mkdir()

    source_dir = tmp_path / 'source'
    source_dir.mkdir()

    output_image_path = source_dir / 'output.jpg'
    used_image_path = source_dir / 'used.jpg'
    output_image_path.touch()
    used_image_path.touch()

    result = {
        'output_image': 'output.jpg',
        'used_image': 'used.jpg',
        'output_image_path': str(output_image_path),
        'used_image_path': str(used_image_path)
    }

    monkeypatch.setattr(file_utils.config, 'PROCESSED_FOLDER', 'processed')

    final_output_path, final_used_path = file_utils.move_processed_files(result, str(project_root))

    assert os.path.exists(final_output_path)
    assert os.path.exists(final_used_path)
    assert not os.path.exists(output_image_path)
    assert not os.path.exists(used_image_path)
    assert os.path.basename(final_output_path) == 'output.jpg'
    assert os.path.basename(final_used_path) == 'used.jpg'

def test_create_sample_image_copy(tmp_path):
    project_root = tmp_path
    temp_dir = project_root / 'temp'
    temp_dir.mkdir()

    demo_dir = project_root / 'static' / 'demo'
    demo_dir.mkdir(parents=True)
    sample_image = demo_dir / 'A.JPG'
    sample_image.write_text('dummy content')

    filepath, filename, file_size = file_utils.create_sample_image_copy(str(project_root), str(temp_dir))

    assert filename == 'A.JPG'
    assert os.path.exists(filepath)
    assert file_size == len('dummy content')
    assert os.path.basename(filepath) == 'A.JPG'