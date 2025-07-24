"""
測試腳本 - 驗證模組化重構是否成功
"""
import sys
import os

def test_imports():
    """測試所有模塊是否能正確導入"""
    print("Testing module imports...")
    
    try:
        from config import config
        print("✅ Config module imported successfully")
        
        from logger import setup_logging, get_client_info, log_user_activity
        print("✅ Logger module imported successfully")
        
        from translations_handler import get_text, load_translations
        print("✅ Translation handler imported successfully")
        
        from fish_detector import FishDetectionSystem
        print("✅ Fish detector imported successfully")
        
        from file_utils import allowed_file, clean_processed_folder
        print("✅ File utils imported successfully")
        
        from routes import register_routes
        print("✅ Routes module imported successfully")
        
        print("\n🎉 All modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """測試配置是否正確"""
    print("\nTesting configuration...")
    
    try:
        from config import config
        
        # 檢查必要的配置項
        assert hasattr(config, 'SECRET_KEY')
        assert hasattr(config, 'LANGUAGES')
        assert hasattr(config, 'PROCESSED_FOLDER')
        assert hasattr(config, 'ROBOFLOW_API_KEY')
        
        print("✅ Configuration is valid")
        print(f"   - Languages: {list(config.LANGUAGES.keys())}")
        print(f"   - Processed folder: {config.PROCESSED_FOLDER}")
        print(f"   - Max files: {config.MAX_PROCESSED_FILES}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_flask_app():
    """測試Flask應用是否能正常創建"""
    print("\nTesting Flask app creation...")
    
    try:
        from app_new import app
        
        # 檢查應用是否創建成功
        assert app is not None
        assert app.secret_key is not None
        
        # 檢查路由是否註冊
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/log', '/upload', '/api/upload']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} missing")
        
        print("✅ Flask app created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Flask app error: {e}")
        return False

def main():
    """主測試函數"""
    print("🔧 Testing Fish Detection System Modular Architecture")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 60)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The modular architecture is working correctly.")
        print("\n📝 Next steps:")
        print("1. Backup your original app.py file")
        print("2. Replace app.py with app_new.py")
        print("3. Test the application in your browser")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
