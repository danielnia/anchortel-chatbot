from ragas.testset import TestsetGenerator
from langchain_community.document_loaders import TextLoader
import uuid
import pandas as pd
import os
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    LLMContextRecall,
    FactualCorrectness,
)
from ragas.evaluation import EvaluationDataset, evaluate


# data source for test data generation

file_path = os.path.join("data", "Anchortel_info.txt")#


def generate_reference_questions(num_questions, generator_llm, generator_embeddings, doc_path=file_path):
    loader = TextLoader(doc_path, encoding="utf-8")
    docs = loader.load()
    print("Loaded documents:", len(docs))
    generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    dataset = generator.generate_with_langchain_docs(docs, testset_size=num_questions)
    df = dataset.to_pandas()
    # print(df.head())
    df = df.drop(columns=["reference_contexts", "synthesizer_name"])
    df.index = [str(uuid.uuid4()) for _ in range(len(df))]
    return df  # DataFrame with columns suitable for Excel-like UI


def compute_ragas_metrics(dataset: list, generator_llm):
    evaluation_dataset = EvaluationDataset.from_list(dataset)
    results = evaluate(
        evaluation_dataset,
        metrics=[
            Faithfulness(),
            AnswerRelevancy(),
            ContextPrecision(),
            LLMContextRecall(),
            FactualCorrectness(mode="f1"),
        ],
        llm=generator_llm
    )
    return results


def append_scores_to_dataframe(df, results):
    # Convert scores to DataFrame
    metrics_df = pd.DataFrame(results.scores)
    # Ensure the index is reset for both DataFrames before concatenation
    df = df.reset_index(drop=True)
    metrics_df = metrics_df.reset_index(drop=True)
    # Concatenate the original DataFrame with the metrics DataFrame
    df = pd.concat([df, metrics_df], axis=1)
    return df

# manual test set generation
run = False
if run:
    num_questions = 2
    df = generate_reference_questions(num_questions, doc_path=path)
    #  creates real answers
    results = compute_ragas_metrics(df.to_dict("records"))
    df = append_scores_to_dataframe(df, results)
    df.to_csv("test_set_with_answers.csv", index=False)

