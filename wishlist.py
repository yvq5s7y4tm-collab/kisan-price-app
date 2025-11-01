import streamlit as st
from price_tracking import fetch_price_history
import matplotlib.pyplot as plt

def wishlist():
    st.title("❤️ My Crop Wishlist")

    if "wishlist" not in st.session_state:
        st.session_state["wishlist"] = []

    new_crop = st.text_input("Add a crop to your wishlist", "")
    if st.button("Add"):
        if new_crop and new_crop not in st.session_state["wishlist"]:
            st.session_state["wishlist"].append(new_crop)
            st.success(f"{new_crop} added to wishlist!")

    st.subheader("🌿 Saved Crops:")
    if st.session_state["wishlist"]:
        for crop in st.session_state["wishlist"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🌱 *{crop}*")
            with col2:
                if st.button(f"📈 View Prices for {crop}", key=crop):
                    show_crop_chart(crop)
    else:
        st.info("No crops added yet.")


def show_crop_chart(crop):
    """Display price chart of selected crop"""
    state = st.selectbox(f"Select State for {crop}", [
        "Maharashtra", "Punjab", "Uttar Pradesh", "Karnataka", "Gujarat", "Haryana", "Madhya Pradesh"
    ], key=f"state_{crop}")

    df = fetch_price_history(state, crop)
    if not df.empty:
        st.success(f"✅ Showing {crop} price trend in {state}")

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(df["arrival_date"], df["modal_price"], marker="o", linestyle="-", color="green")
        ax.set_title(f"{crop} Price Trend in {state}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Modal Price (₹/Quintal)")
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.warning("No data found for this crop in the selected state.")