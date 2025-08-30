from PIL import Image

import cli
import engines


def _fake_dispatch(op, **kwargs):
    if op == "image_to_text":
        return "text", []
    if op == "text_to_dwc":
        return {}, {}
    raise ValueError(op)


def test_process_cli_invokes_preprocess_when_enabled(monkeypatch, tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (10, 10), "white").save(img_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cfg_file = tmp_path / "cfg.toml"
    cfg_file.write_text('[preprocess]\npipeline=["grayscale"]\n')

    called = {"n": 0}

    def fake_preprocess(path, cfg):
        called["n"] += 1
        return path

    monkeypatch.setattr(cli, "preprocess_image", fake_preprocess)
    monkeypatch.setattr(cli, "dispatch", _fake_dispatch)
    monkeypatch.setattr(engines, "dispatch", _fake_dispatch)

    cli.process_cli(tmp_path, out_dir, cfg_file)
    assert called["n"] == 1


def test_process_cli_skips_preprocess_when_disabled(monkeypatch, tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (10, 10), "white").save(img_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    cfg_file = tmp_path / "cfg.toml"
    cfg_file.write_text("[preprocess]\npipeline=[]\n")

    called = {"n": 0}

    def fake_preprocess(path, cfg):
        called["n"] += 1
        return path

    monkeypatch.setattr(cli, "preprocess_image", fake_preprocess)
    monkeypatch.setattr(cli, "dispatch", _fake_dispatch)
    monkeypatch.setattr(engines, "dispatch", _fake_dispatch)

    cli.process_cli(tmp_path, out_dir, cfg_file)
    assert called["n"] == 0
