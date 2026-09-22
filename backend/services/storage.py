from pathlib import Path
from uuid import uuid4
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _extension(filename):
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def save_asset(file_storage, folder='furnivo/uploads'):
    if not file_storage or not file_storage.filename:
        raise ValueError('Choose an image file.')
    extension = _extension(file_storage.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError('Only PNG, JPG, JPEG and WEBP images are supported.')

    if current_app.config.get('CLOUDINARY_URL'):
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(cloudinary_url=current_app.config['CLOUDINARY_URL'])
        root_folder = str(current_app.config.get('CLOUDINARY_FOLDER', 'furnivo')).strip('/') or 'furnivo'
        child_folder = folder.split('/', 1)[-1] if '/' in folder else folder
        result = cloudinary.uploader.upload(
            file_storage,
            folder=f'{root_folder}/{child_folder.strip("/")}',
            resource_type='image',
            transformation=[{'quality': 'auto', 'fetch_format': 'auto'}],
        )
        return {'url': result['secure_url'], 'provider': 'cloudinary', 'public_id': result.get('public_id')}

    safe_name = secure_filename(file_storage.filename)
    filename = f'{uuid4().hex[:12]}-{safe_name}'
    target = Path(current_app.config['UPLOAD_FOLDER']) / filename
    file_storage.save(target)
    return {'url': f'/uploads/{filename}', 'provider': 'local', 'filename': filename}


def save_product_image(file_storage):
    return save_asset(file_storage, folder='furnivo/products')
