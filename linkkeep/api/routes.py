"""REST 路由：书签的增删查 + 标签概览。"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..core.tags import tag_counts
from .deps import get_store
from .schemas import BookmarkIn, BookmarkOut, TagCount

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("", response_model=List[BookmarkOut])
def list_bookmarks(tag: Optional[str] = None, store=Depends(get_store)):
    bookmarks = store.load()
    if tag:
        bookmarks = [b for b in bookmarks if b.matches_tag(tag)]
    return [BookmarkOut(**b.to_dict()) for b in bookmarks]


@router.post("", response_model=BookmarkOut, status_code=201)
def create_bookmark(payload: BookmarkIn, store=Depends(get_store)):
    bm = store.add(url=payload.url, title=payload.title, tags=payload.tags)
    return BookmarkOut(**bm.to_dict())


@router.delete("/{bookmark_id}", status_code=204)
def delete_bookmark(bookmark_id: int, store=Depends(get_store)):
    ok = store.remove(bookmark_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"bookmark {bookmark_id} not found")


@router.get("/tags", response_model=List[TagCount])
def list_tag_counts(store=Depends(get_store)):
    counts = tag_counts(store.load())
    return [TagCount(tag=t, count=c) for t, c in counts.most_common()]
