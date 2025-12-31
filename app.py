import streamlit as st 
import pandas as pd 
import sys
from pathlib import Path
from src.modules.literature import LiteratureSearch, LITERATURE_AVAILABLE

#add src directory to sys.path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.modules.data_loader import DataLoader
from src.modules.synthesizer import SyntheticGenerator
from src.modules.stress_test import QualityReport

#page setup
st.title("🧬 SynthLab v0.1")
st.write("Generate privacy-safe synthetic data from your datasets")

tab1, tab2 = st.tabs (["🔬 Synthetic Data", "📚 Literature Search"])

#synthesizer selection
with st.sidebar:
    st.header("⚙️ Settings")
    method= st.selectbox(
        "Choose a synthesizer method",
        options=["CTGAN", "GaussianCopula", "TVAE"],
        help= "CTGAN is a generative adversarial network that can capture complex dependencies in the data. GaussianCopula is a probabilistic model that can handle both categorical and continuous data. TVAE is a variational autoencoder that can generate synthetic data with a similar distribution to the real data.",
        index=0
    )

    #input for number of synthetic rows
    num_rows = st.number_input("Number of synthetic rows to generate", min_value=1, max_value=10000, value=1000)

#initialize session state
if 'result' not in st.session_state:
    st.session_state.result = {}

with tab1: 
    #file uploader
    uploaded_files = st.file_uploader("Upload your CSV file", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.divider()
            st.subheader(f"📁 {uploaded_file.name}")

            #read CSV file
            df = pd.read_csv(uploaded_file)
            st.write(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")

            #show data preview
            with st.expander("Show Data Preview"):
                st.dataframe(df.head())


            #generate buttons
            if st.button(f"🚀 Processing for {uploaded_file.name}", key=uploaded_file.name):
                with st.spinner(f"Generating synthetic data for {uploaded_file.name}..."):
                    #clean data 
                    loader = DataLoader()
                    clean_df, cols = loader.clean_data(df)

                    #generate synthetic data
                    generator = SyntheticGenerator(method=method)
                    generator.train(clean_df)
                    synthetic_data = generator.generate(num_rows)

                    #store result in session state
                    st.session_state.result[uploaded_file.name] = {
                        'clean_data': clean_df,
                        'synthetic_data': synthetic_data,
                    }

                st.success(f"Generated {len(synthetic_data)} synthetic rows!")

            #show synthetic data preview
            if uploaded_file.name in st.session_state.result:
                result = st.session_state.result[uploaded_file.name]
                clean_df = result['clean_data']
                synthetic_data = result['synthetic_data']
                
                with st.expander("Synthetic Data Preview"):
                    st.dataframe(synthetic_data.head())

                #download link for synthetic data
                csv = synthetic_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Synthetic Data as CSV",
                    data=csv,
                    file_name='synthetic_data.csv',
                    mime='text/csv',
                    key=f"csv_{uploaded_file.name}"
                )

                #quality report
                quality_report = QualityReport(clean_df, synthetic_data)

                #convert report to DataFrame for better display
                with st.expander("📊Quality Report"):
                    stats = quality_report.compare_stats()
                    st.dataframe(pd.DataFrame(stats).T)

                with st.expander("🔒 Privacy Check"):
                    privacy_check = quality_report.check_privacy()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Real Rows", privacy_check["total_real_rows"])
                    col2.metric("Synthetic Rows", privacy_check["total_synthetic_rows"])
                    col3.metric("Leaked Rows", privacy_check['leaked_rows'])

                    if privacy_check["leaked_rows"] > 0:
                        st.warning(f"⚠️ Privacy Score: {privacy_check['leaked_percentage']}% - {privacy_check['leaked_rows']} rows leaked! Consider adjusting the model parameters or using a different synthesizer.")
                    else:
                        st.success(f"✅ Privacy Score: {privacy_check['leaked_percentage']}% - The synthetic data appears to be privacy-safe.")

                #plot distributions
                st.subheader("📈 Distribution Plots")
                figures = quality_report.plot_distributions()
                for col, fig in figures.items():
                    st.divider()
                    st.plotly_chart(fig, use_container_width=True)
                

                #correlation heatmaps
                st.divider()
                st.subheader("🔗 Correlation Heatmaps")
                fig_real, fig_synth, fig_diff = quality_report.plot_correlation_heatmaps()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Real Data Correlation Heatmap**")
                    st.plotly_chart(fig_real, use_container_width=True)
                with col2:
                    st.markdown("**Synthetic Data Correlation Heatmap**")
                    st.plotly_chart(fig_synth, use_container_width=True)

                st.markdown("**Difference in Correlation Heatmap**")
                st.plotly_chart(fig_diff, use_container_width=True)


                #download quality report
                st.divider()
                st.subheader("📥 Export Report")
                pdf_bytes = quality_report.export_report("quality_report.pdf")
                st.download_button(
                    label="Download Quality Report as PDF",
                    data=pdf_bytes,
                    file_name="quality_report.pdf",
                    mime="application/pdf",
                    key = f"unique_name_{uploaded_file.name}"
                )

                #ks test
                with st.expander("📉 KS Test (Statistical Similarity)"):
                    ks_results = quality_report.ks_test()
                    ks_df = pd.DataFrame(ks_results).T

                    #color code results
                    st.dataframe(ks_df)

                    st.write("KS Test Results:")
                    st.write("If the p-value is greater than 0.05, the distributions are considered similar.")
                    st.write("If the p-value is less than 0.05, the distributions are considered different.")

                    similar_count = sum(1 for v in ks_results.values() if v['similar'] == 'True')
                    total_count = len(ks_results)
                    st.write(f"Number of similar distributions (p > 0.05): {similar_count}/{total_count}")

                #Privacy analysis

                with st.expander("🔒 Privacy Analysis"):
                    privacy_analysis = quality_report.check_privacy()
                    dcr = quality_report.distance_to_closest_record()

                    st.write("**Exact Matches in Synthetic Data:**")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Real Rows", privacy_analysis['total_real_rows'])
                    col2.metric("Total Synthetic Rows", privacy_analysis['total_synthetic_rows'])  
                    col3.metric("Percentage Leaked", f"{privacy_analysis['leaked_percentage']}%")

                    st.divider()
                    st.write("**Distance to Closest Record (DCR) Analysis:**")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Minimum DCR", f"{dcr['min_distance']:.4f}")
                    col2.metric("Maximum DCR", f"{dcr['max_distance']:.4f}") 
                    col3.metric("Average DCR", f"{dcr['mean_distance']:.4f}")
                    col4.metric("Too Close Percentage", f"{dcr['too_close_percentage']}%")

                    if dcr['too_close_percentage'] < 5:
                        st.success(f"✅ Strong - {dcr['close_records']} records are sufficiently different from real records.")
                    else:
                        st.warning(f"⚠️ Weak/ Privacy Risk - {dcr['close_records']} records are too similar to real records.")

                with st.expander("⚖️ Fairness Flip Test"):
                    st.write("Assessing fairness by checking for outcome flips in sensitive attributes between real and synthetic data.")

                    #user pick sensitive attribute
                    numeric_cols = synthetic_data.select_dtypes(include=['number']).columns.tolist()
                    flip_col = st.selectbox("Select Sensitive Attribute for Fairness Flip Test", options=numeric_cols)

                    #only show columns with 2 unique values
                    binary_cols = [col for col in numeric_cols if synthetic_data[col].nunique() == 2]

                    if binary_cols:
                        flip_col = st.selectbox("Select Binary Sensitive Attribute for Fairness Flip Test", binary_cols, key=f"flip_{uploaded_file.name}")
                    
                        if st.button("Run Fairness Flip Test", key=f"flip_btn_{uploaded_file.name}"):
                            flip_results = quality_report.flip_test(flip_col)
                        
                            col1, col2 = st.columns(2)
                            col1.metric(f"Group{flip_results['group_a_value']}", flip_results['group_a_count'])
                            col2.metric(f"Group{flip_results['group_b_value']}", flip_results['group_b_count'])

                            st.write(f"**Fairness Score** {flip_results['fairness_score']}%")
                            st.write(f"**Columns with >20% difference: {flip_results['total_biased_columns']}")

                            flip_df = pd.DataFrame(flip_results['column_stats']).T
                            st.dataframe(flip_df)

                    else:
                        st.info("No binary columns available for Fairness Flip Test.")

with tab2: 
    #literature search
    st.header("📚 Literature Intelligence")

    if not LITERATURE_AVAILABLE:
        st.error("Required libraries for Literature Search are not installed. Please install PyPDF2 and sentence-transformers.")
    else:
        #initialize literature search
        if 'literature_search' not in st.session_state:
            st.session_state.literature_search = None
        
        uploaded_pdf = st.file_uploader("Upload a PDF of research papers", type=["pdf"], accept_multiple_files=True, key="pdf_uploader")

        if uploaded_pdf:
            if st.button("📖 Index Papers"):
                with st.spinner("Processing PDF and indexing..."):
                    if st.session_state.literature_search is None:
                        st.session_state.literature_search = LiteratureSearch()

                    for pdf_file in uploaded_pdf:
                        pages = st.session_state.literature_search.add_pdf_bytes(pdf_file.read(), pdf_file.name)
                        st.success(f"Indexed {pages} pages from {pdf_file.name}.")
            #show query input
            if st.session_state.literature_search:
                stats = st.session_state.literature_search.get_stats()
                st.write(f"**Indexed:** {stats['num_pages']} pages from {stats['num_documents']} files")

            #search query
            if st.session_state.literature_search and st.session_state.literature_search.documents:
                st.subheader("🔍 Search Literature")
                query = st.text_input("Enter search query: ", placeholder="e.g., synthetic data privacy", key="literature_query")

                if query:
                    results = st.session_state.literature_search.search(query, top_k=5)

                    if results:
                        #AI generated summary
                        st.subheader("📝 Quick Summary")
                        with st.spinner("Generating summary...."):
                            summary= st.session_state.literature_search.summarize_results(query, results)
                        st.write(summary)

                        st.divider()
                        st.subheader ("📄 Source Documents")

                        for i, result in enumerate(results):
                            with st.expander(f"Result {i+1} - {result['filename']} - Score: {result['score']:.4f}"):
                                #tabs for preview vs full texts
                                preview_tab, full_tab = st.tabs(["Preview", "Full Text"])

                                with preview_tab:
                                    st.write(result['text_snippet'])
                                with full_tab:
                                    st.write(result['text'])

                                #copy button
                                st.code(result['text'][:500], language = None)
                        else:
                            st.info("No relevant sections found for the given query.")



