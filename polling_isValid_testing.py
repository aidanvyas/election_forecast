import pandas as pd
from typing import List


def compare_llm_with_final(llm_filenames: List[str], final_filenames: List[str], output_filename: str) -> None:
    """
    Compare the LLM and final CSV files and write the results to a file.

    Parameters:
        llm_filenames List[str]: A list of filenames for the LLM CSV files.
        final_filenames List[str]: A list of filenames for the final CSV files.
        output_filename str: The name of the output file to write the results to.

    Returns:
        None
    """

    # Initialize variables to store the results.
    total_questions = 0
    correct_predictions = 0
    success_rate = 0

    with open(output_filename, 'w') as file:

        # Iterate over the LLM and final filenames.
        for i in range(len(llm_filenames)):

            # Read in the LLM and final CSV files.
            llm_df = pd.read_csv(llm_filenames[i])
            final_df = pd.read_csv(final_filenames[i])

            # Sort the dataframes by QuestionID.
            llm_df = llm_df.sort_values('QuestionID')
            final_df = final_df.sort_values('QuestionID')

            # Merge the LLM and final dataframes on the common columns.
            merged_df = pd.merge(llm_df, final_df, on=['QuestionID', 'RespTxt', 'RespPct', 'QuestionTxt', 'QuestionNote', 'SubPopulation', 'ReleaseDate', 'SurveyOrg', 'SurveySponsor', 'SourceDoc', 'BegDate', 'EndDate', 'ExactDates', 'SampleDesc', 'SampleSize', 'VariableName', 'IntMethod', 'StudyNote'], suffixes=('_llm', '_final'))

            # Find disagreements between the LLM and final dataframes.
            disagreements = merged_df[merged_df['isValid_llm'] != merged_df['isValid_final']]

            # If there are disagreements, write them.
            if not disagreements.empty:
                file.write("\nDisagreements:\n")

                # Group the disagreements by QuestionID.
                grouped_disagreements = disagreements.groupby('QuestionID')

                # Iterate over the questions.
                for question_id, group in grouped_disagreements:

                    # Write the question information.
                    question_text = group['QuestionTxt'].iloc[0]
                    file.write(f"\nQuestionID: {question_id}\n")
                    file.write(f"QuestionTxt: {question_text}\n")
                    file.write("Responses:\n")

                    # Iterate over the responses.
                    for _, row in group.iterrows():

                        # Write the response information.
                        file.write(f"{row['RespTxt']} ({row['RespPct']}%)\n")
                    file.write(f"isValid_llm: {row['isValid_llm']}\n")
                    file.write(f"isValid_final: {row['isValid_final']}\n\n")

            # Update the total questions and correct predictions.
            total_questions += merged_df['QuestionID'].nunique()
            correct_predictions += (merged_df.groupby('QuestionID')['isValid_llm'].first() == merged_df.groupby('QuestionID')['isValid_final'].first()).sum()

        # Calculate the success rate.
        success_rate = (correct_predictions / total_questions) * 100

        # Write the results.
        file.write(f"Success Rate: {success_rate:.2f}%\n")
        file.write(f"Number of errors: {total_questions - correct_predictions}\n")
        file.write(f"Total questions: {total_questions}\n")
