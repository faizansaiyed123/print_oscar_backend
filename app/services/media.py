from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.media import MediaAsset, UploadedCustomerFile
from app.repositories.admin import AdminRepository
from app.utils.files import save_upload, safe_relative_storage_path


class MediaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AdminRepository(session)

    async def list_media_assets(self, page: int = 1, page_size: int = 50):
        return await self.repository.list_media_assets(page=page, page_size=page_size)

    async def upload_media_asset(
        self,
        upload: UploadFile,
        *,
        product_id: int | None = None,
        category_id: int | None = None,
        alt_text: str | None = None,
        is_public: bool = True,
    ) -> MediaAsset:
        stored_path, file_size = await save_upload(upload, "media")
        asset = MediaAsset(
            product_id=product_id,
            category_id=category_id,
            file_name=upload.filename or Path(stored_path).name,
            file_path=Path(stored_path).name,
            mime_type=upload.content_type or "application/octet-stream",
            file_size=file_size,
            alt_text=alt_text,
            is_public=is_public,
        )
        await self.repository.save(asset)
        await self.session.commit()
        await self.session.refresh(asset)
        return asset

    async def delete_media_asset(self, media_id: int) -> None:
        asset = await self.repository.get_media_asset(media_id)
        if not asset:
            raise AppException("Media asset not found", 404)
        file_path = Path(settings.media_root) / "media" / asset.file_path
        if file_path.exists():
            file_path.unlink()
        await self.repository.delete(asset)
        await self.session.commit()

    async def upload_customer_file(
        self,
        upload: UploadFile,
        *,
        field_type: str,
        order_item_id: int | None = None,
        user_id: int | None = None,
        product_id: int | None = None,
    ) -> UploadedCustomerFile:
        stored_path, file_size = await save_upload(upload, "customer-uploads")
        customer_file = UploadedCustomerFile(
            order_item_id=order_item_id,
            user_id=user_id,
            product_id=product_id,
            file_name=upload.filename or Path(stored_path).name,
            file_path=safe_relative_storage_path(stored_path),
            mime_type=upload.content_type or "application/octet-stream",
            file_size=file_size,
            preview_url=safe_relative_storage_path(stored_path),
            field_type=field_type,
        )
        await self.repository.save(customer_file)
        await self.session.commit()
        await self.session.refresh(customer_file)
        return customer_file

    async def delete_customer_file(self, file_id: int) -> None:
        customer_file = await self.repository.get_uploaded_customer_file(file_id)
        if not customer_file:
            raise AppException("Customer file not found", 404)
        file_path = Path(settings.media_root) / customer_file.file_path
        if file_path.exists():
            file_path.unlink()
        await self.repository.delete(customer_file)
        await self.session.commit()

    async def compress_media_asset(self, media_id: int) -> dict[str, str]:
        asset = await self.repository.get_media_asset(media_id)
        if not asset:
            raise AppException("Media asset not found", 404)
        return {"message": f"Compression queued for {asset.file_name}"}
