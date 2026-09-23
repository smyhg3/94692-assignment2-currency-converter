"""Simple Streamlit interface for Frankfurter currency conversion."""

from datetime import date

import streamlit as st

from currency import convert_amount, format_conversion_result, inverse_rate, validate_amount
from frankfurter import get_currencies, get_historical_rate, get_latest_rate, get_three_year_rates


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
    show_conversion_section("Latest", source, target, amount)
    show_conversion_section("Historical", source, target, amount)
    st.markdown("Project repository: [GitHub](https://github.com/smyhg3/94692-assignment2-currency-converter)")
    st.caption("If you find this project useful, feel free to leave a ⭐ — it’s free! 😋")


def show_conversion_section(section, source, target, amount):
    """Render one independent result area using the shared conversion workflow."""
    st.subheader(f"{section} exchange rate")
    is_historical = section == "Historical"
    historical_date = None
    if is_historical:
        historical_date = st.date_input(
            "Historical date", value=date.today(),
            min_value=date(1999, 1, 4), max_value=date.today(),
        )
        st.caption("If no rate was published that day, an earlier working day's rate may be returned.")

    # Separate keys preserve both results across Streamlit reruns.
    result_key = f"{section.lower()}_result"
    if st.button(f"Get {section.lower()} conversion rate"):
        # Clear only this section when a new request fails.
        st.session_state[result_key] = None
        try:
            if source == target:
                raise ValueError("Please choose two different currencies.")
            if is_historical:
                if historical_date is None:
                    raise ValueError("Please select a valid historical date.")
                if historical_date > date.today():
                    raise ValueError("Historical date must not be in the future.")
            validate_amount(amount)
            with st.spinner("Retrieving exchange rate..."):
                if is_historical:
                    quote = get_historical_rate(source, target, historical_date.isoformat())
                else:
                    quote = get_latest_rate(source, target)
                converted = convert_amount(amount, quote["rate"])
                inverse = inverse_rate(quote["rate"])
            result = {
                "text": format_conversion_result(
                    quote["date"], source, target, quote["rate"], amount, converted, inverse
                ),
                "date": quote["date"],
                "requested_date": historical_date.isoformat() if historical_date else None,
                "pair": (source, target),
            }
            st.session_state[result_key] = result
            if section == "Latest":
                # A trend failure must not discard a successful conversion.
                try:
                    with st.spinner("Retrieving three-year rate trend..."):
                        result["trend"] = get_three_year_rates(source, target)
                except (ValueError, RuntimeError):
                    result["trend"] = []
        except ValueError as error:
            st.error(str(error))
        except RuntimeError as error:
            st.error(f"Unable to retrieve an exchange rate. {error}")

    result = st.session_state.get(result_key)
    if result:
        st.write(f"Exchange rate date: {result['date']}")
        if result["requested_date"] and result["date"] != result["requested_date"]:
            st.info(f"Requested date: {result['requested_date']}. The available rate date is shown above.")
    st.text_area(
        f"{section} conversion result", value=result["text"] if result else "",
        height=140, disabled=True,
    )
    if section == "Latest" and result:
        st.subheader("Rate Trend Over the Last 3 years")
        if result.get("pair") != (source, target):
            st.info("Click Get latest conversion rate to show the trend for the selected currencies.")
        elif not result.get("trend"):
            st.warning("Three-year trend data is unavailable. Please try Get latest conversion rate again later.")
        else:
            st.caption(f"{source} → {target}: target currency units per 1 {source}")
            st.line_chart(
                {"Date": [row["Date"] for row in result["trend"]],
                 "Rate": [row["Rate"] for row in result["trend"]]},
                x="Date", y="Rate", x_label="Date", y_label="Rate",
            )


if __name__ == "__main__":
    main()
