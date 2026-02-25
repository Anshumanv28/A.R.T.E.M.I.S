#!/usr/bin/env python3
"""
Collection Management CLI

Utility script for managing Qdrant collections:
- List all collections
- Get collection information
- Delete collections
- Clear collections (remove all points but keep collection)
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import artemis
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.rag.core.collection_manager import (
    list_collections,
    get_collection_info,
    delete_collection,
    clear_collection,
    create_collection
)
from artemis.utils import get_logger

logger = get_logger(__name__)


def cmd_list(args):
    """List all collections."""
    try:
        collections = list_collections()
        
        if not collections:
            print("No collections found in Qdrant.")
            return
        
        print(f"\nFound {len(collections)} collection(s):\n")
        for i, name in enumerate(collections, 1):
            try:
                info = get_collection_info(name)
                print(f"{i}. {name}")
                print(f"   Points: {info.get('points_count', 'N/A')}")
                print(f"   Status: {info.get('status', 'N/A')}")
                print()
            except Exception as e:
                print(f"{i}. {name} (error getting info: {e})")
                print()
        
    except Exception as e:
        print(f"❌ Failed to list collections: {e}")
        logger.exception("List collections failed", exc_info=True)
        sys.exit(1)


def cmd_info(args):
    """Get information about a collection."""
    if not args.collection:
        print("❌ Collection name is required")
        print("Usage: python scripts/manage_collections.py info <collection_name>")
        sys.exit(1)
    
    try:
        info = get_collection_info(args.collection)
        
        print(f"\nCollection: {args.collection}")
        print("-" * 50)
        print(f"Points Count: {info.get('points_count', 'N/A')}")
        print(f"Vectors Count: {info.get('vectors_count', 'N/A')}")
        print(f"Status: {info.get('status', 'N/A')}")
        print()
        
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to get collection info: {e}")
        logger.exception("Get collection info failed", exc_info=True)
        sys.exit(1)


def cmd_delete(args):
    """Delete a collection."""
    if not args.collection:
        print("❌ Collection name is required")
        print("Usage: python scripts/manage_collections.py delete <collection_name>")
        sys.exit(1)
    
    # Confirmation prompt
    if not args.yes:
        response = input(
            f"⚠️  WARNING: This will permanently delete collection '{args.collection}' and all its data.\n"
            f"   This action cannot be undone!\n\n"
            f"   Type 'DELETE' to confirm: "
        )
        if response != "DELETE":
            print("❌ Deletion cancelled.")
            sys.exit(0)
    
    try:
        delete_collection(args.collection, confirm=True)
        print(f"✅ Successfully deleted collection '{args.collection}'")
        
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to delete collection: {e}")
        logger.exception("Delete collection failed", exc_info=True)
        sys.exit(1)


def cmd_clear(args):
    """Clear all points from a collection."""
    if not args.collection:
        print("❌ Collection name is required")
        print("Usage: python scripts/manage_collections.py clear <collection_name>")
        sys.exit(1)
    
    # Confirmation prompt
    if not args.yes:
        try:
            info = get_collection_info(args.collection)
            points_count = info.get('points_count', 0)
        except:
            points_count = "unknown"
        
        response = input(
            f"⚠️  WARNING: This will permanently delete all {points_count} points from collection '{args.collection}'.\n"
            f"   The collection will remain but will be empty.\n"
            f"   This action cannot be undone!\n\n"
            f"   Type 'CLEAR' to confirm: "
        )
        if response != "CLEAR":
            print("❌ Clearing cancelled.")
            sys.exit(0)
    
    try:
        clear_collection(args.collection, confirm=True)
        print(f"✅ Successfully cleared collection '{args.collection}'")
        
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to clear collection: {e}")
        logger.exception("Clear collection failed", exc_info=True)
        sys.exit(1)


def cmd_create(args):
    """Create a new collection."""
    if not args.collection:
        print("❌ Collection name is required")
        print("Usage: python scripts/manage_collections.py create <collection_name> [--dim <dimension>]")
        sys.exit(1)
    
    try:
        create_collection(
            args.collection,
            embedding_dim=args.dimension
        )
        print(f"✅ Successfully created collection '{args.collection}'")
        
        # Show collection info
        info = get_collection_info(args.collection)
        print(f"   Points: {info.get('points_count', 0)}")
        print(f"   Status: {info.get('status', 'N/A')}")
        
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        logger.exception("Create collection failed", exc_info=True)
        sys.exit(1)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Manage Qdrant collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all collections
  python scripts/manage_collections.py list
  
  # Get collection info
  python scripts/manage_collections.py info my_collection
  
  # Delete a collection (with confirmation)
  python scripts/manage_collections.py delete my_collection
  
  # Delete without confirmation prompt
  python scripts/manage_collections.py delete my_collection --yes
  
  # Clear all points from a collection
  python scripts/manage_collections.py clear my_collection
  
  # Create a new collection
  python scripts/manage_collections.py create my_collection
  python scripts/manage_collections.py create my_collection --dim 768
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all collections')
    list_parser.set_defaults(func=cmd_list)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get collection information')
    info_parser.add_argument('collection', nargs='?', help='Collection name')
    info_parser.set_defaults(func=cmd_info)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a collection')
    delete_parser.add_argument('collection', nargs='?', help='Collection name')
    delete_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    delete_parser.set_defaults(func=cmd_delete)
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all points from a collection')
    clear_parser.add_argument('collection', nargs='?', help='Collection name')
    clear_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    clear_parser.set_defaults(func=cmd_clear)
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new collection')
    create_parser.add_argument('collection', nargs='?', help='Collection name')
    create_parser.add_argument('--dim', '--dimension', type=int, dest='dimension', help='Embedding dimension (default: 384 for all-MiniLM-L6-v2)')
    create_parser.set_defaults(func=cmd_create)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
