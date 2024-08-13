def format_number(number):
    if number >= 1e12:
        return f"{number / 1e12:.2f} Trillion"
    elif number >= 1e9:
        return f"{number / 1e9:.2f} Billion"
    elif number >= 1e6:
        return f"{number / 1e6:.2f} Million"
    else:
        return str(number)

def risk_analysis(liquidity_data, holders_data, threshold):
    risk_score = 0
    liquidity = liquidity_data.get("liquidity")
    holder = holders_data[0] if holders_data else {}

    if liquidity is not None and liquidity < threshold:
        risk_score += 1

    if holder and holder.get("amount", 0) > 0.1:
        risk_score += 1

    return risk_score
