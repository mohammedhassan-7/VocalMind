import os
import argparse
import sys
from pathlib import Path

# Helper script to list and download model artifacts from DagsHub MLflow

def setup_mlflow():
    # Try to load environment variables from local .env files
    try:
        from dotenv import load_dotenv
        # Look for .env in current directory or parent directory
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        load_dotenv()
    except ImportError:
        pass

    # Fallback default configurations if not defined in .env or shell environment
    if not os.getenv("MLFLOW_TRACKING_URI"):
        os.environ["MLFLOW_TRACKING_URI"] = "https://dagshub.com/jalalqassas/vocalMind.mlflow"
    if not os.getenv("MLFLOW_TRACKING_USERNAME"):
        os.environ["MLFLOW_TRACKING_USERNAME"] = "jalalqassas"

    # Verify tracking password is set
    tracking_pwd = os.getenv("MLFLOW_TRACKING_PASSWORD")
    if not tracking_pwd or tracking_pwd.strip() in {"", "your_token"}:
        print("[ERROR] MLFLOW_TRACKING_PASSWORD is not set in your environment or .env file.")
        print("Please configure MLFLOW_TRACKING_PASSWORD with your DagsHub Personal Access Token first.")
        sys.exit(1)
    
    try:
        import mlflow
        mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
        return mlflow
    except ImportError:
        print("[ERROR] mlflow is not installed. Install it with: pip install mlflow")
        sys.exit(1)


def list_runs(mlflow):
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    experiment_name = "customer-agent-classification"
    
    print(f"Connecting to DagsHub MLflow experiment: '{experiment_name}'...")
    try:
        exp = client.get_experiment_by_name(experiment_name)
        if not exp:
            print(f"[ERROR] Experiment '{experiment_name}' not found.")
            return
        
        runs = client.search_runs(experiment_ids=[exp.experiment_id])
        print(f"\nFound {len(runs)} runs:")
        print(f"{'Run ID':<36} | {'Run Name':<45} | {'F1-Score':<10} | {'Accuracy':<10}")
        print("-" * 109)
        for run in runs[:30]:  # Show top 30 runs
            run_name = run.data.tags.get("mlflow.runName", "Unnamed")
            f1 = run.data.metrics.get("f1", "N/A")
            acc = run.data.metrics.get("accuracy", "N/A")
            
            # Format outputs
            f1_str = f"{f1:.4f}" if isinstance(f1, float) else str(f1)
            acc_str = f"{acc:.4f}" if isinstance(acc, float) else str(acc)
            
            print(f"{run.info.run_id:<36} | {run_name:<45} | {f1_str:<10} | {acc_str:<10}")
    except Exception as e:
        print(f"[ERROR] Failed to list runs: {e}")

def download_model(mlflow, run_id, output_dir):
    from mlflow.artifacts import download_artifacts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    artifact_uri = f"runs:/{run_id}/model"
    print(f"Attempting to download artifacts from: {artifact_uri}")
    print(f"Destination folder: {output_path.resolve()}")
    
    try:
        local_path = download_artifacts(artifact_uri=artifact_uri, dst_path=str(output_path))
        print(f"\n[SUCCESS] Model successfully downloaded to: {local_path}")
    except Exception as e:
        print(f"\n[ERROR] Failed to download model programmatically: {e}")
        print("\n[TIP] This error might occur if the model artifacts were not uploaded correctly during training or if remote storage authentication failed.")
        print("You can download the model manually from the DagsHub Web UI:")
        print(f"1. Navigate to: https://dagshub.com/jalalqassas/vocalMind.mlflow/#/experiments/0/runs/{run_id}")
        print("2. Scroll down to the 'Artifacts' section.")
        print("3. Click on the 'model' directory, and download 'model.pkl' and 'MLmodel'.")
        print(f"4. Move the downloaded files to: {output_path.resolve()}/")

def main():
    parser = argparse.ArgumentParser(description="Retrieve and manage agent-customer classifier models from DagsHub MLflow.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List available runs and experiments on MLflow tracking server.")
    group.add_argument("--run-id", type=str, help="The MLflow Run ID to download model artifacts from.")
    parser.add_argument("--output-dir", type=str, default="services/whisperx/models/speaker_role",
                        help="Local directory where the downloaded model files will be stored.")
    
    args = parser.parse_args()
    
    mlflow = setup_mlflow()
    
    if args.list:
        list_runs(mlflow)
    elif args.run-id:
        download_model(mlflow, args.run_id, args.output_dir)

if __name__ == "__main__":
    main()
