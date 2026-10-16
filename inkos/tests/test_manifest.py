import pytest, yaml, os
from onovel import manifest as mf
def test_scaffold_valid(book):
    m = mf.load(book); assert m["genre_id"] == "tien-hiep" and "tôi" in m["xung_ho"]["forbidden_for"]["tu sĩ"]
def test_unknown_genre(book):
    m = mf.load(book); m["genre_id"] = "khong-co"
    with pytest.raises(mf.ManifestError): mf.validate(m)
def test_missing_field(book):
    m = mf.load(book); del m["register"]
    with pytest.raises(mf.ManifestError): mf.validate(m)
def test_missing_manifest(tmp_path):
    with pytest.raises(mf.ManifestError): mf.load(str(tmp_path))
def test_skills_reads_manifest_no_guessing(book):
    import skills; bid, key, s = skills.resolve(book); assert key == "tien-hiep" and s["skills"]
    os.remove(os.path.join(book, "onovel.yaml"))
    with pytest.raises(mf.ManifestError): skills.resolve(book)
def test_real_books_manifests():
    root = "/CODE/inkos-books/xemtruyen/books"
    if not os.path.isdir(root): pytest.skip("no local books")
    for b in ("tuc-the", "dieu-khoan-gia-han", "tien-tro", "pham-nhan-nghich-thien-luc"): mf.load(os.path.join(root, b))
