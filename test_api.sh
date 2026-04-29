#!/bin/bash
API=$1
IMAGE="system-images;android-${API};google_apis;x86_64"
NAME="test_api${API}"

source /Users/andyawd/Project/android-cli-mac-x86-community/.venv/bin/activate

echo ">>> [API $API] Installing SDK and System Image..."
android-cli-mac-x86-community sdk install "$IMAGE" "platforms;android-${API}" > /dev/null

echo ">>> [API $API] Creating AVD..."
android-cli-mac-x86-community emulator create --name "$NAME" --image "$IMAGE" --force > /dev/null

echo ">>> [API $API] Starting AVD..."
android-cli-mac-x86-community emulator start --name "$NAME"
adb wait-for-device

echo ">>> [API $API] Waiting for boot..."
BOOTED=0
for i in {1..150}; do
  COMPLETED=`adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r'`
  ANIM=`adb shell getprop init.svc.bootanim 2>/dev/null | tr -d '\r'`
  if [ "$COMPLETED" == "1" ] && [ "$ANIM" == "stopped" ]; then
    BOOTED=1
    break
  fi
  sleep 2
done

if [ $BOOTED -eq 0 ]; then
  echo "!!! [API $API] Stuck on boot."
  android-cli-mac-x86-community emulator stop --name "$NAME"
  exit 1
fi

echo ">>> [API $API] Booted successfully. Unlocking screen..."
sleep 5
adb shell input keyevent 82
adb shell input keyevent 4

echo ">>> [API $API] Installing and running Test App..."
android-cli-mac-x86-community run --apks /tmp/RealTestApp/app/build/outputs/apk/debug/app-debug.apk --activity com.example.realtestapp/.MainActivity

echo ">>> [API $API] Waiting 10s for app to render..."
sleep 10

echo ">>> [API $API] Capturing screenshot..."
android-cli-mac-x86-community screen capture --output /tmp/screenshot_api${API}.png
ls -lh /tmp/screenshot_api${API}.png

echo ">>> [API $API] Stopping AVD..."
android-cli-mac-x86-community emulator stop --name "$NAME"
echo ">>> [API $API] Test completed successfully!"
