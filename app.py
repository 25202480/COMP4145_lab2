import streamlit as st
import plotly.graph_objects as go

from trading_strategy import (
    analyze_results,
    calculate_moving_averages,
    get_stock_data,
    identify_golden_cross,
    implement_strategy,
)


st.set_page_config(
    page_title="Trading Strategy Dashboard",
    page_icon="📈",
    layout="wide",
)


@st.cache_data(show_spinner="Downloading market data...")
def load_strategy_data():
    data = get_stock_data("MSFT")
    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions


def build_price_chart(data, positions):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name="Close price",
            line={"color": "#2f80ed", "width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA50"],
            mode="lines",
            name="Short-term MA (50 days)",
            line={"color": "#f2994a", "width": 1.5},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA200"],
            mode="lines",
            name="Long-term MA (200 days)",
            line={"color": "#9b51e0", "width": 1.5},
        )
    )

    if not positions.empty:
        figure.add_trace(
            go.Scatter(
                x=positions["BuyDate"],
                y=positions["BuyPrice"],
                mode="markers",
                name="Buy",
                marker={"color": "#27ae60", "size": 11, "symbol": "triangle-up"},
                customdata=positions["ProfitPct"],
                hovertemplate="Buy: %{x}<br>Price: %{y:.2f}<br>"
                "Trade result: %{customdata:.2f}%<extra></extra>",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=positions["SellDate"],
                y=positions["SellPrice"],
                mode="markers",
                name="Sell",
                marker={"color": "#eb5757", "size": 11, "symbol": "triangle-down"},
                hovertemplate="Sell: %{x}<br>Price: %{y:.2f}<extra></extra>",
            )
        )

    figure.update_layout(
        title="MSFT Price and Golden-Cross Trades",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.02, "x": 0},
        height=650,
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
    )
    return figure


def show_chart_page(data, positions):
    st.header("Price Chart")
    st.caption("The chart covers the complete downloaded period.")
    st.plotly_chart(build_price_chart(data, positions), use_container_width=True)


def show_statistics_page(positions):
    st.header("Overall Trade Statistics")
    if positions.empty:
        st.warning("No trading signals were detected for this period.")
        return

    total_trades = len(positions)
    winning_trades = int((positions["ProfitPct"] > 0).sum())
    losing_trades = total_trades - winning_trades
    win_rate = winning_trades / total_trades * 100
    average_profit = positions["ProfitPct"].mean()
    target_reached = int((positions["SellReason"] == "Target reached").sum())

    metrics = st.columns(5)
    metrics[0].metric("Total trades", total_trades)
    metrics[1].metric("Winning trades", winning_trades)
    metrics[2].metric("Losing trades", losing_trades)
    metrics[3].metric("Win rate", f"{win_rate:.2f}%")
    metrics[4].metric("Average profit", f"{average_profit:.2f}%")

    st.subheader("Trade outcome summary")
    st.write(f"Target reached: **{target_reached}**")
    st.write(
        "Maximum holding period exits: "
        f"**{total_trades - target_reached}**"
    )


def show_details_page(positions):
    st.header("Detailed Trades")
    if positions.empty:
        st.warning("No trading signals were detected for this period.")
        return

    display_positions = positions.copy()
    for column in ("BuyDate", "SellDate"):
        display_positions[column] = display_positions[column].dt.strftime(
            "%Y-%m-%d"
        )
    display_positions["BuyPrice"] = display_positions["BuyPrice"].map(
        lambda value: f"{value:.2f}"
    )
    display_positions["SellPrice"] = display_positions["SellPrice"].map(
        lambda value: f"{value:.2f}"
    )
    display_positions["ProfitPct"] = display_positions["ProfitPct"].map(
        lambda value: f"{value:.2f}%"
    )
    display_positions = display_positions.rename(
        columns={
            "BuyDate": "Buy date",
            "BuyPrice": "Buy price",
            "SellDate": "Sell date",
            "SellPrice": "Sell price",
            "HoldingDays": "Holding days",
            "ProfitPct": "Profit",
            "SellReason": "Sell reason",
        }
    )
    st.dataframe(display_positions, hide_index=True, use_container_width=True)


def main():
    st.sidebar.title("Trading Strategy")
    page = st.sidebar.radio(
        "Navigate",
        ("Price chart", "Trade statistics", "Detailed trades"),
    )

    try:
        data, positions = load_strategy_data()
    except Exception as error:
        st.error(f"Could not load trading data: {error}")
        st.stop()

    if page == "Price chart":
        show_chart_page(data, positions)
    elif page == "Trade statistics":
        show_statistics_page(positions)
    else:
        show_details_page(positions)


if __name__ == "__main__":
    main()
