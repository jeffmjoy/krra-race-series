"""Tests for export module."""

import csv

from krra_race_series.export import ResultsExporter
from krra_race_series.scoring import AgeGroup, RacePoints, SeriesTotal


def test_export_to_csv(tmp_path):
    """Test exporting series totals to CSV."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            total_points=190,
            race_details=[],
        ),
        SeriesTotal(
            member_id="M002",
            member_name="Jane Smith",
            races_completed=1,
            total_points=100,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "results.csv"
    exporter.export_to_csv(totals, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]
        assert rows[1] == ["1", "M001", "John Doe", "2", "190"]
        assert rows[2] == ["2", "M002", "Jane Smith", "1", "100"]


def test_sanitize_csv_field_with_formula_injection():
    """Test that CSV fields are sanitized to prevent formula injection."""
    exporter = ResultsExporter()

    # Test various formula injection patterns
    assert exporter._sanitize_csv_field("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert exporter._sanitize_csv_field("+1+1") == "'+1+1"
    assert exporter._sanitize_csv_field("-5") == "'-5"
    assert exporter._sanitize_csv_field("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert exporter._sanitize_csv_field("\t1+1") == "'\t1+1"
    assert exporter._sanitize_csv_field("\r1+1") == "'\r1+1"

    # Test normal values that should not be modified
    assert exporter._sanitize_csv_field("John Doe") == "John Doe"
    assert exporter._sanitize_csv_field("123") == "123"
    assert exporter._sanitize_csv_field(42) == 42
    assert exporter._sanitize_csv_field(3.14) == 3.14
    assert exporter._sanitize_csv_field("") == ""


def test_export_to_csv_creates_parent_directory(tmp_path):
    """Test that export creates parent directories if they don't exist."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=1,
            total_points=100,
            race_details=[],
        ),
    ]

    # Use a nested path that doesn't exist
    output_path = tmp_path / "nested" / "dir" / "results.csv"
    exporter.export_to_csv(totals, output_path)

    assert output_path.exists()


def test_export_to_csv_with_formula_injection_in_data(tmp_path):
    """Test that CSV export sanitizes malicious data."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="=CMD|'/c calc'!A1",
            member_name="+1+1",
            races_completed=1,
            total_points=100,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "results.csv"
    exporter.export_to_csv(totals, output_path)

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Verify that dangerous values are prefixed with a single quote
        assert rows[1][1] == "'=CMD|'/c calc'!A1"
        assert rows[1][2] == "'+1+1"


def test_export_detailed_csv_with_race_details(tmp_path):
    """Test exporting detailed CSV with race-by-race breakdown."""
    exporter = ResultsExporter()

    race_points = [
        RacePoints(
            member_id="M001",
            race_name="Spring 5K",
            overall_place=5,
            overall_points=96,
            age_group=AgeGroup.AGE_30_39,
            age_group_place=2,
            age_group_points=10,
        ),
        RacePoints(
            member_id="M001",
            race_name="Summer 8K",
            overall_place=10,
            overall_points=91,
            age_group=AgeGroup.AGE_30_39,
            age_group_place=3,
            age_group_points=8,
        ),
    ]

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            total_points=205,
            race_details=race_points,
        ),
    ]

    output_path = tmp_path / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Check header
        assert rows[0] == [
            "Rank",
            "Member ID",
            "Name",
            "Race",
            "Overall Place",
            "Overall Points",
            "Age Group",
            "Age Group Place",
            "Age Group Points",
            "Race Total",
            "Series Total",
        ]

        # Check first race detail
        assert rows[1][0] == "1"  # Rank
        assert rows[1][1] == "M001"  # Member ID
        assert rows[1][2] == "John Doe"  # Name
        assert rows[1][3] == "Spring 5K"  # Race
        assert rows[1][4] == "5"  # Overall Place
        assert rows[1][5] == "96"  # Overall Points
        assert rows[1][6] == "30-39"  # Age Group
        assert rows[1][7] == "2"  # Age Group Place
        assert rows[1][8] == "10"  # Age Group Points
        assert rows[1][9] == "106"  # Race Total
        assert rows[1][10] == "205"  # Series Total

        # Check second race detail
        assert rows[2][3] == "Summer 8K"
        assert rows[2][6] == "30-39"  # Age group format


def test_export_detailed_csv_with_no_race_details(tmp_path):
    """Test exporting detailed CSV for members with no races."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=0,
            total_points=0,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Should have one data row with empty race fields
        assert rows[1][0] == "1"  # Rank
        assert rows[1][1] == "M001"  # Member ID
        assert rows[1][2] == "John Doe"  # Name
        assert rows[1][3] == ""  # Empty race fields
        assert rows[1][10] == "0"  # Series Total


def test_export_detailed_csv_with_no_age_group(tmp_path):
    """Test exporting detailed CSV with race results that have no age group."""
    exporter = ResultsExporter()

    race_points = [
        RacePoints(
            member_id="M001",
            race_name="Spring 5K",
            overall_place=5,
            overall_points=96,
            age_group=None,
            age_group_place=None,
            age_group_points=0,
        ),
    ]

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=1,
            total_points=96,
            race_details=race_points,
        ),
    ]

    output_path = tmp_path / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Age group fields should be empty
        assert rows[1][6] == ""  # Age Group
        assert rows[1][7] == ""  # Age Group Place


def test_export_detailed_csv_creates_parent_directory(tmp_path):
    """Test that detailed export creates parent directories if they don't exist."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=0,
            total_points=0,
            race_details=[],
        ),
    ]

    # Use a nested path that doesn't exist
    output_path = tmp_path / "nested" / "dir" / "detailed_results.csv"
    exporter.export_detailed_csv(totals, output_path)

    assert output_path.exists()


def test_export_category_standings(tmp_path):
    """Test exporting category standings to separate files."""
    exporter = ResultsExporter()

    category_standings = {
        "M_overall": [
            SeriesTotal(
                member_id="M001",
                member_name="John Doe",
                races_completed=3,
                total_points=225,
                race_details=[],
            ),
            SeriesTotal(
                member_id="M003",
                member_name="Bob Jones",
                races_completed=2,
                total_points=150,
                race_details=[],
            ),
        ],
        "F_overall": [
            SeriesTotal(
                member_id="M002",
                member_name="Jane Smith",
                races_completed=2,
                total_points=180,
                race_details=[],
            ),
        ],
        "M_30-39": [
            SeriesTotal(
                member_id="M001",
                member_name="John Doe",
                races_completed=3,
                total_points=45,
                race_details=[],
            ),
        ],
    }

    output_dir = tmp_path / "category_results"
    exporter.export_category_standings(category_standings, output_dir)

    # Check that all category files were created
    assert (output_dir / "M_overall.csv").exists()
    assert (output_dir / "F_overall.csv").exists()
    assert (output_dir / "M_30-39.csv").exists()

    # Verify M_overall content
    with open(output_dir / "M_overall.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]
        assert rows[1] == ["1", "M001", "John Doe", "3", "225"]
        assert rows[2] == ["2", "M003", "Bob Jones", "2", "150"]

    # Verify F_overall content
    with open(output_dir / "F_overall.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[1] == ["1", "M002", "Jane Smith", "2", "180"]

    # Verify M_30-39 content
    with open(output_dir / "M_30-39.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[1] == ["1", "M001", "John Doe", "3", "45"]


def test_export_category_standings_creates_directory(tmp_path):
    """Test that category export creates output directory if it doesn't exist."""
    exporter = ResultsExporter()

    category_standings = {
        "M_overall": [
            SeriesTotal(
                member_id="M001",
                member_name="John Doe",
                races_completed=1,
                total_points=100,
                race_details=[],
            ),
        ],
    }

    output_dir = tmp_path / "nested" / "category" / "results"
    exporter.export_category_standings(category_standings, output_dir)

    assert output_dir.exists()
    assert (output_dir / "M_overall.csv").exists()


def test_export_category_standings_with_formula_injection(tmp_path):
    """Test that category export sanitizes malicious data."""
    exporter = ResultsExporter()

    category_standings = {
        "M_overall": [
            SeriesTotal(
                member_id="=FORMULA()",
                member_name="+1+1",
                races_completed=1,
                total_points=100,
                race_details=[],
            ),
        ],
    }

    output_dir = tmp_path / "results"
    exporter.export_category_standings(category_standings, output_dir)

    with open(output_dir / "M_overall.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[1][1] == "'=FORMULA()"
        assert rows[1][2] == "'+1+1"


def test_export_category_standings_empty_category(tmp_path):
    """Test exporting category with no members."""
    exporter = ResultsExporter()

    category_standings = {
        "M_overall": [],
    }

    output_dir = tmp_path / "results"
    exporter.export_category_standings(category_standings, output_dir)

    # File should be created with just header
    with open(output_dir / "M_overall.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 1  # Only header
        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]


def test_export_category_standings_all_age_groups(tmp_path):
    """Test exporting all possible age/gender category combinations."""
    exporter = ResultsExporter()

    # Create standings for all standard categories
    category_standings = {}
    for gender in ["M", "F"]:
        for age_group in [
            "overall",
            "U20",
            "20-29",
            "30-39",
            "40-49",
            "50-59",
            "60-69",
            "70-79",
            "80+",
        ]:
            category_name = f"{gender}_{age_group}"
            category_standings[category_name] = [
                SeriesTotal(
                    member_id=f"{gender}001",
                    member_name=f"Test {gender} {age_group}",
                    races_completed=1,
                    total_points=50,
                    race_details=[],
                ),
            ]

    output_dir = tmp_path / "all_categories"
    exporter.export_category_standings(category_standings, output_dir)

    # Verify all 18 category files exist (9 age groups x 2 genders)
    expected_files = [
        "M_overall.csv",
        "F_overall.csv",
        "M_U20.csv",
        "F_U20.csv",
        "M_20-29.csv",
        "F_20-29.csv",
        "M_30-39.csv",
        "F_30-39.csv",
        "M_40-49.csv",
        "F_40-49.csv",
        "M_50-59.csv",
        "F_50-59.csv",
        "M_60-69.csv",
        "F_60-69.csv",
        "M_70-79.csv",
        "F_70-79.csv",
        "M_80+.csv",
        "F_80+.csv",
    ]

    for filename in expected_files:
        assert (output_dir / filename).exists(), f"Missing file: {filename}"


def test_export_to_csv_with_race_columns(tmp_path):
    """Test exporting to CSV with individual race columns instead of Races count."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            total_points=180,
            race_details=[],
            race_points_by_race={"Spring 5K": 90, "Summer 8K": 90},
        ),
        SeriesTotal(
            member_id="M002",
            member_name="Jane Smith",
            races_completed=1,
            total_points=88,
            race_details=[],
            race_points_by_race={"Spring 5K": 88},
        ),
    ]

    output_path = tmp_path / "results.csv"
    race_names = ["Spring 5K", "Summer 8K"]
    exporter.export_to_csv(totals, output_path, race_names)

    assert output_path.exists()

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Check header has race columns
        assert rows[0] == [
            "Rank",
            "Member ID",
            "Name",
            "Spring 5K",
            "Summer 8K",
            "Total Points",
        ]
        # John participated in both races
        assert rows[1] == ["1", "M001", "John Doe", "90", "90", "180"]
        # Jane only participated in Spring 5K
        assert rows[2] == ["2", "M002", "Jane Smith", "88", "", "88"]


def test_export_to_csv_with_race_columns_empty_values(tmp_path):
    """Test CSV export with race columns shows empty strings for non-participation."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=1,
            total_points=75,
            race_details=[],
            race_points_by_race={"Race 2": 75},  # Only participated in Race 2
        ),
    ]

    output_path = tmp_path / "results.csv"
    race_names = ["Race 1", "Race 2", "Race 3"]
    exporter.export_to_csv(totals, output_path, race_names)

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        assert rows[0] == [
            "Rank",
            "Member ID",
            "Name",
            "Race 1",
            "Race 2",
            "Race 3",
            "Total Points",
        ]
        # Race 1 and Race 3 should be empty
        assert rows[1] == ["1", "M001", "John Doe", "", "75", "", "75"]


def test_export_to_csv_without_race_names_uses_races_column(tmp_path):
    """Test that export falls back to 'Races' column when race_names not provided."""
    exporter = ResultsExporter()

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            total_points=180,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "results.csv"
    exporter.export_to_csv(totals, output_path)  # No race_names

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Should use the old format with Races column
        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]
        assert rows[1] == ["1", "M001", "John Doe", "2", "180"]


def test_export_category_standings_with_race_columns(tmp_path):
    """Test category standings export with individual race columns."""
    exporter = ResultsExporter()

    category_standings = {
        "M_overall": [
            SeriesTotal(
                member_id="M001",
                member_name="John Doe",
                races_completed=2,
                total_points=146,
                race_details=[],
                race_points_by_race={"Spring 5K": 75, "Summer 8K": 71},
            ),
            SeriesTotal(
                member_id="M002",
                member_name="Bob Jones",
                races_completed=1,
                total_points=73,
                race_details=[],
                race_points_by_race={"Spring 5K": 73},
            ),
        ],
    }

    output_dir = tmp_path / "category_results"
    race_names = ["Spring 5K", "Summer 8K"]
    exporter.export_category_standings(category_standings, output_dir, race_names)

    with open(output_dir / "M_overall.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Header should have race columns
        assert rows[0] == [
            "Rank",
            "Member ID",
            "Name",
            "Spring 5K",
            "Summer 8K",
            "Total Points",
        ]
        assert rows[1] == ["1", "M001", "John Doe", "75", "71", "146"]
        assert rows[2] == ["2", "M002", "Bob Jones", "73", "", "73"]


def test_export_category_standings_without_race_names(tmp_path):
    """Test category standings falls back to Races column when race_names not given."""
    exporter = ResultsExporter()

    category_standings = {
        "M_overall": [
            SeriesTotal(
                member_id="M001",
                member_name="John Doe",
                races_completed=3,
                total_points=225,
                race_details=[],
            ),
        ],
    }

    output_dir = tmp_path / "results"
    exporter.export_category_standings(category_standings, output_dir)  # No race_names

    with open(output_dir / "M_overall.csv") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Should use old format
        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Total Points"]
        assert rows[1] == ["1", "M001", "John Doe", "3", "225"]


def test_export_total_points_equals_sum_of_race_columns(tmp_path):
    """Test that total points equals the sum of individual race points columns."""
    exporter = ResultsExporter()

    race_points = {"Race 1": 75, "Race 2": 73, "Race 3": 71}
    expected_total = sum(race_points.values())

    totals = [
        SeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=3,
            total_points=expected_total,
            race_details=[],
            race_points_by_race=race_points,
        ),
    ]

    output_path = tmp_path / "results.csv"
    race_names = ["Race 1", "Race 2", "Race 3"]
    exporter.export_to_csv(totals, output_path, race_names)

    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Parse the race columns and verify they sum to total
        race_1 = int(rows[1][3])
        race_2 = int(rows[1][4])
        race_3 = int(rows[1][5])
        total = int(rows[1][6])

        assert race_1 + race_2 + race_3 == total
        assert total == expected_total


def test_export_age_graded_standings(tmp_path):
    """Test exporting age-graded standings to CSV."""
    from krra_race_series.age_grading import AgeGradedSeriesTotal

    exporter = ResultsExporter()

    standings = [
        AgeGradedSeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=2,
            average_age_graded_percentage=95.5,
            race_details=[],
        ),
        AgeGradedSeriesTotal(
            member_id="F001",
            member_name="Jane Smith",
            races_completed=1,
            average_age_graded_percentage=98.2,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "age_graded.csv"
    exporter.export_age_graded_standings(standings, output_path)

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Check header
        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Avg Age-Graded %"]

        # Check first member
        assert rows[1][0] == "1"
        assert rows[1][1] == "M001"
        assert rows[1][2] == "John Doe"
        assert rows[1][3] == "2"
        assert rows[1][4] == "95.50"

        # Check second member
        assert rows[2][0] == "2"
        assert rows[2][1] == "F001"
        assert rows[2][2] == "Jane Smith"
        assert rows[2][3] == "1"
        assert rows[2][4] == "98.20"


def test_export_age_graded_standings_creates_directory(tmp_path):
    """Test that export creates output directory if it doesn't exist."""
    from krra_race_series.age_grading import AgeGradedSeriesTotal

    exporter = ResultsExporter()

    standings = [
        AgeGradedSeriesTotal(
            member_id="M001",
            member_name="John Doe",
            races_completed=1,
            average_age_graded_percentage=95.5,
            race_details=[],
        ),
    ]

    output_path = tmp_path / "subdir" / "age_graded.csv"
    exporter.export_age_graded_standings(standings, output_path)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_export_age_graded_standings_empty(tmp_path):
    """Test exporting empty age-graded standings."""
    exporter = ResultsExporter()

    standings = []

    output_path = tmp_path / "age_graded.csv"
    exporter.export_age_graded_standings(standings, output_path)

    # File should be created with just header
    with open(output_path) as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 1  # Only header
        assert rows[0] == ["Rank", "Member ID", "Name", "Races", "Avg Age-Graded %"]
