"""Simple Streamlit interface for Frankfurter currency conversion."""

from datetime import date

import streamlit as st

from currency import convert_amount, inverse_rate, validate_amount
from frankfurter import get_currencies, get_historical_rate, get_latest_rate


@st.cache_data(ttl=3600)
def load_currencies():
    """Cache the API currency list for one hour."""
    return get_currencies()


def main():
    """Collect conversion inputs and display the backend's results."""
    st.title("Currency Converter")
    st.write("Convert currencies using exchange rates from Frankfurter.")

    try:
        currencies = load_currencies()
    except RuntimeError as error:
        st.error(f"Unable to load currencies. {error}")
        if st.button("Retry loading currencies"):
            st.rerun()
        return

    codes = sorted(currencies)
    source = st.selectbox(
        "Source currency", codes,
        index=codes.index("AUD") if "AUD" in codes else 0,
        format_func=lambda code: f"{code} — {currencies[code]}",
    )
    target = st.selectbox(
        "Target currency", codes,
        index=codes.index("USD") if "USD" in codes else min(1, len(codes) - 1),
        format_func=lambda code: f"{code} — {currencies[code]}",
    )
    amount = st.number_input("Amount", min_value=0.0, value=100.0, step=1.0)
    st.caption("Enter a non-negative amount. A zero amount converts to zero.")
    mode = st.radio("Exchange rate", ["Latest exchange rate", "Historical exchange rate"])
    historical_date = None
    if mode == "Historical exchange rate":
        historical_date = st.date_input(
            "Historical date", value=date.today(),
            min_value=date(1999, 1, 4), max_value=date.today(),
        )
        st.caption("If no rate was published that day, an earlier working day's rate may be returned.")

    if not st.button("Convert"):
        return
    if source == target:
        st.error("Please choose two different currencies.")
        return
    if mode == "Historical exchange rate" and historical_date is None:
        st.error("Please select a valid historical date.")
        return
    if historical_date is not None and historical_date > date.today():
        st.error("Historical date must not be in the future.")
        return

    try:
        validate_amount(amount)
        with st.spinner("Retrieving exchange rate..."):
            if mode == "Historical exchange rate":
                quote = get_historical_rate(source, target, historical_date.isoformat())
            else:
                quote = get_latest_rate(source, target)
            converted = convert_amount(amount, quote["rate"])
            inverse = inverse_rate(quote["rate"])
    except ValueError as error:
        st.error(str(error))
        return
    except RuntimeError as error:
        st.error(f"Unable to retrieve an exchange rate. {error}")
        return

    st.subheader("Conversion result")
    st.write(f"Exchange rate date: {quote['date']}")
    if historical_date is not None and quote["date"] != historical_date.isoformat():
        st.info(f"Requested date: {historical_date.isoformat()}. The available rate date is shown above.")
    result_text = (
        f"The conversion rate on {quote['date']} from {source} to {target} "
        f"was {quote['rate']:.6g}. So {amount:,.2f} in {source} correspond to "
        f"{converted:,.2f} in {target}. The inverse rate was {inverse:.6g}."
    )
    st.text_area("Conversion result details", value=result_text, height=140, disabled=True)


if __name__ == "__main__":
    main()
