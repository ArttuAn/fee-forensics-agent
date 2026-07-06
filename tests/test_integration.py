"""Integration tests for end-to-end workflows."""

import json
from pathlib import Path
import pytest

from finance_agent.ingest import read_statement_csv
from finance_agent.analysis import audit
from finance_agent.reporting import render_markdown, extract_caps_from_text
from finance_agent.export import render_json
from finance_agent.config import Config, get_config


class TestEndToEndAudit:
    """Test complete audit workflow from CSV to report."""
    
    def test_full_audit_workflow(self, tmp_path):
        """Test complete audit workflow with sample data."""
        # Arrange
        statement_path = Path("sample-data/statement.csv")
        output_path = tmp_path / "report.md"
        
        # Act
        transactions = read_statement_csv(statement_path)
        report = audit(transactions, flag_threshold_abs=25.0)
        markdown = render_markdown(report)
        output_path.write_text(markdown, encoding="utf-8")
        
        # Assert
        assert len(transactions) > 0
        assert report.fee_total >= 0
        assert report.interest_total >= 0
        assert output_path.exists()
        assert "Fee Forensics" in markdown
    
    def test_audit_with_agreement_workflow(self, tmp_path):
        """Test audit workflow with agreement file."""
        # Arrange
        statement_path = Path("sample-data/statement.csv")
        agreement_path = Path("sample-data/agreement.txt")
        output_path = tmp_path / "report-with-agreement.md"
        
        # Act
        transactions = read_statement_csv(statement_path)
        report = audit(transactions, flag_threshold_abs=25.0)
        agreement_text = agreement_path.read_text(encoding="utf-8")
        caps = extract_caps_from_text(agreement_text)
        markdown = render_markdown(report, agreement=caps)
        output_path.write_text(markdown, encoding="utf-8")
        
        # Assert
        assert len(caps) >= 0
        assert output_path.exists()
        assert "Fee Forensics" in markdown
    
    def test_json_export_workflow(self, tmp_path):
        """Test JSON export workflow."""
        # Arrange
        statement_path = Path("sample-data/statement.csv")
        output_path = tmp_path / "report.json"
        
        # Act
        transactions = read_statement_csv(statement_path)
        report = audit(transactions, flag_threshold_abs=25.0)
        json_output = render_json(report, version="0.5.0")
        output_path.write_text(json_output, encoding="utf-8")
        
        # Assert
        assert output_path.exists()
        data = json.loads(json_output)
        assert data["version"] == "0.5.0"
        assert "fee_total" in data
        assert "interest_total" in data


class TestConfigurationWorkflow:
    """Test configuration management workflow."""
    
    def test_default_config_workflow(self):
        """Test workflow with default configuration."""
        # Act
        config = get_config()
        
        # Assert
        assert config.flag_threshold_abs == 25.0
        assert config.flag_threshold_pct == 0.05
        assert config.output_dir == "reports"
    
    def test_config_from_dict_workflow(self):
        """Test workflow with custom configuration."""
        # Arrange
        config_dict = {
            "flag_threshold_abs": 50.0,
            "flag_threshold_pct": 0.10,
            "output_dir": "custom_reports",
            "log_level": "DEBUG",
        }
        
        # Act
        config = Config(**config_dict)
        
        # Assert
        assert config.flag_threshold_abs == 50.0
        assert config.flag_threshold_pct == 0.10
        assert config.output_dir == "custom_reports"
    
    def test_config_to_dict_workflow(self):
        """Test configuration serialization."""
        # Arrange
        config = Config(flag_threshold_abs=30.0, log_level="WARNING")
        
        # Act
        config_dict = config.to_dict()
        
        # Assert
        assert config_dict["flag_threshold_abs"] == 30.0
        assert config_dict["log_level"] == "WARNING"
    
    def test_config_yaml_workflow(self, tmp_path):
        """Test YAML configuration workflow."""
        # Arrange
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "flag_threshold_abs: 40.0\n"
            "flag_threshold_pct: 0.08\n"
            "output_dir: yaml_reports\n"
            "log_level: DEBUG\n",
            encoding="utf-8"
        )
        
        # Act
        config = Config.from_yaml(config_path)
        
        # Assert
        assert config.flag_threshold_abs == 40.0
        assert config.flag_threshold_pct == 0.08
        assert config.output_dir == "yaml_reports"
        assert config.log_level == "DEBUG"


class TestErrorHandlingWorkflow:
    """Test error handling in workflows."""
    
    def test_invalid_statement_workflow(self):
        """Test workflow with invalid statement file."""
        # Arrange
        invalid_path = Path("nonexistent.csv")
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            read_statement_csv(invalid_path)
    
    def test_empty_statement_workflow(self, tmp_path):
        """Test workflow with empty statement."""
        # Arrange
        empty_path = tmp_path / "empty.csv"
        empty_path.write_text("date,description,amount\n", encoding="utf-8")
        
        # Act
        transactions = read_statement_csv(empty_path)
        report = audit(transactions, flag_threshold_abs=25.0)
        
        # Assert
        assert len(transactions) == 0
        assert report.fee_total == 0.0
        assert report.interest_total == 0.0
