"""Publisher archive headings must not override the actual course term suffix."""

from scripts.discover_business_physics_resources import econ_candidates, newest_outlines


def test_economics_winter_archive_keeps_fall_and_winter_course_sections_separate():
    html = """<h3>Courses offered Winter 2025–2026</h3><table>
    <tr><td>ECO101H1F Principles of Microeconomics • Calendar entry</td></tr>
    <tr><td><a href="/index.php/index/teaching/downloadCourseOutline/7239/997904079">Outline</a></td></tr>
    <tr><td>ECO101H1S Principles of Microeconomics • Calendar entry</td></tr>
    <tr><td><a href="/index.php/index/teaching/downloadCourseOutline/7241/997905772">Outline</a></td></tr>
    </table>"""
    rows = econ_candidates(html, "https://www.economics.utoronto.ca/", {"ECO101H1"})
    assert [row["academic_period"] for row in rows] == ["Fall 2025", "Winter 2026"]
    assert len(newest_outlines(rows)) == 2


def test_economics_summer_subsessions_do_not_become_fall_or_winter():
    html = """<h3>Courses offered Summer 2025</h3><table>
    <tr><td>ECO101H1F Principles of Microeconomics • Calendar entry</td></tr>
    <tr><td><a href="/index.php/index/teaching/downloadCourseOutline/7245/997901261">Outline</a></td></tr>
    </table>"""
    rows = econ_candidates(html, "https://www.economics.utoronto.ca/", {"ECO101H1"})
    assert rows[0]["academic_period"] == "Summer 2025 (F section)"
