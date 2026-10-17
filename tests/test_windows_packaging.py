"""Packaging trust boundaries, independent of a Windows execution host."""
import hashlib
from pathlib import Path

import pytest


def test_corrupt_archive_is_rejected_before_extraction(tmp_path):
    from scripts.windows_native import verify_digest
    archive = tmp_path / 'native.7z'
    archive.write_bytes(b'corrupt download')
    with pytest.raises(ValueError, match='SHA-256'):
        verify_digest(archive, '0' * 64)
    verify_digest(archive, hashlib.sha256(b'corrupt download').hexdigest())


def test_dependency_audit_rejects_unbundled_third_party_dll():
    from scripts.windows_native import validate_imports
    validate_imports(['KERNEL32.dll', 'api-ms-win-crt-runtime-l1-1-0.dll'], ['kernel32.dll'])
    with pytest.raises(ValueError, match='libgcc_s_seh-1.dll'):
        validate_imports(['KERNEL32.dll', 'libgcc_s_seh-1.dll'], ['kernel32.dll'])


def test_package_inventory_rejects_private_or_development_files(tmp_path):
    from scripts.verify_windows import inventory
    (tmp_path / 'Auralume.exe').write_bytes(b'executable fixture')
    (tmp_path / '.env').write_text('SECRET=example')
    with pytest.raises(ValueError, match='.env'):
        inventory(tmp_path)
    (tmp_path / '.env').unlink()
    report = inventory(tmp_path)
    assert report[0]['path'] == 'Auralume.exe'
    assert report[0]['size'] == 18
    assert len(report[0]['sha256']) == 64


def test_zip_relocation_rejects_path_escape(tmp_path):
    from scripts.verify_windows import extract_package
    import zipfile
    archive = tmp_path / 'bad.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('../outside.txt', 'bad')
    with pytest.raises(ValueError, match='Unsafe'):
        extract_package(archive, tmp_path / 'extract')
    assert not (tmp_path / 'outside.txt').exists()


def test_inventory_allows_certifi_public_ca_bundle_but_not_private_pem(tmp_path):
    from scripts.verify_windows import inventory
    certificate = tmp_path / '_internal/certifi/cacert.pem'
    certificate.parent.mkdir(parents=True)
    certificate.write_text('public trust anchors fixture')
    assert len(inventory(tmp_path)) == 1
    (tmp_path / 'private.pem').write_text('private key fixture')
    with pytest.raises(ValueError, match='private.pem'):
        inventory(tmp_path)


def test_acceptance_database_is_committed_and_closed_before_directory_cleanup(tmp_path):
    import sqlite3
    from scripts.verify_windows import open_database
    path = tmp_path / 'library.sqlite3'
    with open_database(path) as connection:
        connection.execute('CREATE TABLE test (value TEXT)')
        connection.execute('INSERT INTO test VALUES (?)', ('Canção',))
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        connection.execute('SELECT 1')
    with open_database(path) as reopened:
        assert reopened.execute('SELECT value FROM test').fetchone() == ('Canção',)
    path.unlink()
    assert not path.exists()
