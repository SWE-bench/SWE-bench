import re
import xml.etree.ElementTree as ET
from swebench.harness.constants import TestStatus
from swebench.harness.test_spec.test_spec import TestSpec


def parse_log_gradle(log: str, test_spec: TestSpec) -> dict[str, str]:
    """
    Parser for test logs generated with Gradle. Supports both JUnit XML output
    and Gradle text output parsing.

    Args:
        log (str): log content
        test_spec (TestSpec): test specification
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}
    passed_tests = set()
    failed_tests = set()
    skipped_tests = set()

    # Try to find the JUnit XML content in the log
    xml_start = log.find('<?xml version="1.0" encoding="UTF-8"?>')
    xml_end = log.find('</testsuites>') + len("</testsuites>")
    if xml_start != -1 and xml_end != -1:
        xml_content = log[xml_start:xml_end]
        try:
            root = ET.fromstring(xml_content)

            # Parse all testsuites and testcases
            for testsuite in root.findall('.//testsuite'):
                for testcase in testsuite.findall('testcase'):
                    classname = testcase.get('classname', '')
                    name = testcase.get('name', '')
                    test_id = f"{classname}.{name}"

                    # Check if test failed
                    failure = testcase.find('failure')
                    error = testcase.find('error')
                    skipped = testcase.find('skipped')

                    if failure is not None or error is not None:
                        failed_tests.add(test_id)
                    elif skipped is not None:
                        skipped_tests.add(test_id)
                    else:
                        passed_tests.add(test_id)

            # Convert to test_status_map
            for test in passed_tests:
                test_status_map[test] = TestStatus.PASSED.value
            for test in failed_tests:
                test_status_map[test] = TestStatus.FAILED.value
            for test in skipped_tests:
                test_status_map[test] = TestStatus.SKIPPED.value

            # Check for static verification success
            if "STATIC VERIFICATION SUCCESS" in log:
                test_status_map["static_verification"] = TestStatus.PASSED.value
            else:
                test_status_map["static_verification"] = TestStatus.FAILED.value

            return test_status_map
        except ET.ParseError:
            pass

    # Fallback to regex-based parsing
    passed_res = [
        re.compile(r"^> Task :(\S+)$"),
        re.compile(r"^> Task :(\S+) UP-TO-DATE$"),
        re.compile(r"^(.+ > .+) PASSED$"),
    ]

    failed_res = [
        re.compile(r"^> Task :(\S+) FAILED$"),
        re.compile(r"^(.+ > .+) FAILED$"),
    ]

    skipped_res = [
        re.compile(r"^> Task :(\S+) SKIPPED$"),
        re.compile(r"^> Task :(\S+) NO-SOURCE$"),
        re.compile(r"^(.+ > .+) SKIPPED$"),
    ]

    for line in log.splitlines():
        for passed_re in passed_res:
            m = passed_re.match(line)
            if m and m.group(1) not in failed_tests:
                passed_tests.add(m.group(1))

        for failed_re in failed_res:
            m = failed_re.match(line)
            if m:
                failed_tests.add(m.group(1))
                if m.group(1) in passed_tests:
                    passed_tests.remove(m.group(1))

        for skipped_re in skipped_res:
            m = skipped_re.match(line)
            if m:
                skipped_tests.add(m.group(1))

    # Convert to test_status_map
    for test in passed_tests:
        test_status_map[test] = TestStatus.PASSED.value
    for test in failed_tests:
        test_status_map[test] = TestStatus.FAILED.value
    for test in skipped_tests:
        test_status_map[test] = TestStatus.SKIPPED.value

    # Check for static verification success
    if "STATIC VERIFICATION SUCCESS" in log:
        test_status_map["static_verification"] = TestStatus.PASSED.value
    else:
        test_status_map["static_verification"] = TestStatus.FAILED.value

    return test_status_map


MAP_REPO_TO_PARSER_KOTLIN = {
    repo: parse_log_gradle
    for repo in [
        "Aliucord/Aliucord",
        "AllanWang/Frost-for-Facebook",
        "AppIntro/AppIntro",
        "DroidKaigi/conference-app-2021",
        "DroidKaigi/conference-app-2023",
        "GetStream/whatsApp-clone-compose",
        "GrapheneOS/Camera",
        "IacobIonut01/Gallery",
        "LemmyNet/jerboa",
        "LibChecker/LibChecker",
        "MMRLApp/MMRL",
        "Mahmud0808/ColorBlendr",
        "NordicSemiconductor/Android-DFU-Library",
        "Pool-Of-Tears/GreenStash",
        "Pool-Of-Tears/Myne",
        "Shabinder/SpotiFlyer",
        "Stypox/dicio-android",
        "T8RIN/ImageToolbox",
        "Tapadoo/Alerter",
        "TrianguloY/URLCheck",
        "android/nowinandroid",
        "android/socialite",
        "android/sunflower",
        "android/uamp",
        "aniyomiorg/aniyomi",
        "avluis/Hentoid",
        "beemdevelopment/Aegis",
        "d4rken-org/capod",
        "flipperdevices/Flipper-Android-App",
        "getodk/collect",
        "gradle/gradle",
        "iSoron/uhabits",
        "jaredsburrows/android-gradle-java-app-template",
        "jarnedemeulemeester/findroid",
        "kasem-sm/SlimeKT",
        "keymapperorg/KeyMapper",
        "kylecorry31/Trail-Sense",
        "leonlatsch/Photok",
        "nextcloud/android",
        "nextcloud/notes-android",
        "owncloud/android",
        "oxygen-updater/oxygen-updater",
        "patzly/grocy-android",
        "recloudstream/cloudstream",
        "spacecowboy/Feeder",
        "thunderbird/thunderbird-android",
        "wikimedia/apps-android-wikipedia",
        "you-apps/ClockYou",
        "you-apps/RecordYou"
    ]
}
