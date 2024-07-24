import pandas as pd


def compare_llm_with_final(llm_filename: str, final_filename: str):
    """
    Compare the LLM and final CSV files and print the success rate and disagreements.

    Parameters:
        llm_filename (str): The filename of the LLM CSV file.
        final_filename (str): The filename of the final CSV file.

    Returns:
        None
    """

    # Read in the LLM and final CSV files.
    llm_df = pd.read_csv(llm_filename)
    final_df = pd.read_csv(final_filename)

    # Sort the dataframes by QuestionID.
    llm_df = llm_df.sort_values('QuestionID')
    final_df = final_df.sort_values('QuestionID')

    # Merge the LLM and final dataframes on the common columns.
    merged_df = pd.merge(llm_df, final_df, on=['QuestionID', 'RespTxt', 'RespPct', 'QuestionTxt', 'QuestionNote', 'SubPopulation', 'ReleaseDate', 'SurveyOrg', 'SurveySponsor', 'SourceDoc', 'BegDate', 'EndDate', 'ExactDates', 'SampleDesc', 'SampleSize', 'VariableName', 'IntMethod', 'StudyNote'], suffixes=('_llm', '_final'))

    # Calculate the success rate.
    total_questions = merged_df['QuestionID'].nunique()
    correct_predictions = (merged_df.groupby('QuestionID')['isValid_llm'].first() == merged_df.groupby('QuestionID')['isValid_final'].first()).sum()
    success_rate = (correct_predictions / total_questions) * 100

    # Find disagreements between the LLM and final dataframes.
    disagreements = merged_df[merged_df['isValid_llm'] != merged_df['isValid_final']]

    # If there are disagreements, print them.
    if not disagreements.empty:
        print("\nDisagreements:")

        # Group the disagreements by QuestionID.
        grouped_disagreements = disagreements.groupby('QuestionID')

        # Iterate over the questions.
        for question_id, group in grouped_disagreements:

            # Print the question information.
            question_text = group['QuestionTxt'].iloc[0]
            print(f"\nQuestionID: {question_id}")
            print(f"QuestionTxt: {question_text}")
            print("Responses:")

            # Iterate over the responses.
            for _, row in group.iterrows():

                # Print the response information.
                print(f"{row['RespTxt']} ({row['RespPct']}%)")
            print(f"isValid_llm: {row['isValid_llm']}")
            print(f"isValid_final: {row['isValid_final']}")
            print()

    # Print the results.
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Number of errors: {total_questions - correct_predictions}")
    print(f"Total questions: {total_questions}")
