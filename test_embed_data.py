#!/usr/bin/env python3
"""
Test script to fetch and display full embed data from Firestore
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'google2', 'adk1', 'nocode'))

from firestore_manager import FirestoreManager

def test_fetch_embed_data():
    """Fetch and display embed data for a specific embed ID"""
    
    # The embed ID from your screenshot
    embed_id = "embed_agent_1757753931906_egs3go_0e243016"
    
    print("🔍 Testing Embed Data Fetch")
    print("=" * 50)
    print(f"📋 Embed ID: {embed_id}")
    print()
    
    try:
        # Initialize Firestore manager
        print("🔧 Initializing Firestore connection...")
        db_manager = FirestoreManager()
        print("✅ Firestore manager initialized")
        print()
        
        # Fetch the specific embed data
        print(f"🔍 Fetching embed data for: {embed_id}")
        embed_data = db_manager.get_agent_embed(embed_id)
        
        if not embed_data:
            print("❌ No embed data found for this ID")
            return
        
        print("✅ Embed data found!")
        print()
        
        # Display the complete embed data
        print("📄 COMPLETE EMBED DATA:")
        print("=" * 50)
        
        # Pretty print the JSON data
        formatted_data = json.dumps(embed_data, indent=2, ensure_ascii=False)
        print(formatted_data)
        print()
        
        # Display specific form fields with labels
        print("📝 FORM DATA BREAKDOWN:")
        print("=" * 50)
        
        form_fields = {
            "Purpose": embed_data.get("purpose"),
            "Custom Purpose": embed_data.get("custom_purpose"),
            "Environment": embed_data.get("environment"),
            "Requests per Hour": embed_data.get("requests_per_hour"),
            "Payload Size": embed_data.get("payload_size"),
            "System URL": embed_data.get("system_url"),
            "Additional URLs": embed_data.get("additional_urls"),
            "Strict Whitelist": embed_data.get("strict_whitelist")
        }
        
        for label, value in form_fields.items():
            print(f"  {label:20}: {value}")
        
        print()
        
        # Display metadata
        print("📊 METADATA:")
        print("=" * 50)
        
        metadata_fields = {
            "Embed ID": embed_data.get("embed_id"),
            "Agent ID": embed_data.get("agent_id"),
            "Agent Name": embed_data.get("agent_name"),
            "Created At": embed_data.get("created_at"),
            "Is Active": embed_data.get("is_active"),
            "Access Count": embed_data.get("access_count"),
            "Last Accessed": embed_data.get("last_accessed")
        }
        
        for label, value in metadata_fields.items():
            print(f"  {label:20}: {value}")
        
        print()
        
        # Test URL whitelist functionality
        print("🔒 URL WHITELIST TEST:")
        print("=" * 50)
        
        system_url = embed_data.get("system_url")
        additional_urls = embed_data.get("additional_urls", [])
        strict_whitelist = embed_data.get("strict_whitelist", False)
        
        print(f"  System URL: {system_url}")
        print(f"  Additional URLs: {additional_urls}")
        print(f"  Strict Whitelist: {strict_whitelist}")
        
        # Show what URLs would be allowed
        allowed_urls = [system_url] if system_url else []
        allowed_urls.extend(additional_urls)
        
        print(f"  Allowed URLs ({len(allowed_urls)}):")
        for i, url in enumerate(allowed_urls, 1):
            print(f"    {i}. {url}")
        
        print()
        
        # Show storage location
        print("🗄️ STORAGE LOCATION:")
        print("=" * 50)
        print(f"  Firestore Path: /agent-genie/agent_embeds/items/{embed_id}")
        print(f"  Collection: agent-genie")
        print(f"  Document: agent_embeds")
        print(f"  Subcollection: items")
        print(f"  Document ID: {embed_id}")
        
        print()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error fetching embed data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch_embed_data()
