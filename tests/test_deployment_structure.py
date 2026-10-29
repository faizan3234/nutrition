"""Basic packaged deployment contract; not a live Docker or security certification."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docker_image_contains_customer_and_admin_apps():
    dockerfile = (ROOT / 'Dockerfile').read_text()
    assert 'COPY web/' in dockerfile
    assert 'COPY admin/' in dockerfile
    assert 'COPY app/' in dockerfile


def test_private_learning_images_are_persistent_and_not_public_assets():
    dockerfile = (ROOT / 'Dockerfile').read_text()
    compose = (ROOT / 'docker-compose.yml').read_text()
    assert 'RELIV_LEARNING_IMAGE_DIR=/srv/data/private_learning_images' in dockerfile
    assert 'RELIV_LEARNING_IMAGE_DIR: /srv/data/private_learning_images' in compose
    assert 'nutrition_data:/srv/data' in compose
    assert 'COPY private_learning_images' not in dockerfile


def test_static_assets_exist_for_both_interfaces():
    for file in ('web/index.html', 'web/app.js', 'web/style.css', 'admin/index.html', 'admin/app.js'):
        assert (ROOT / file).is_file(), file
