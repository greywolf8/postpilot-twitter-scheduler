import pandas as pd
import matplotlib.pyplot as plt


# ================= CONFIG =================

CSV_FILE = "user_analytics.csv"
REPORT_FILE = "analytics_report.txt"


# ================= LOAD DATA =================

def load_data():

    df = pd.read_csv(CSV_FILE)

    # Convert time
    df["created_at"] = pd.to_datetime(df["created_at"])

    # Extract time features
    df["hour"] = df["created_at"].dt.hour
    df["day"] = df["created_at"].dt.day_name()
    df["month"] = df["created_at"].dt.month_name()

    return df


# ================= BASIC INSIGHTS =================

def basic_stats(df):

    stats = {}

    stats["total_posts"] = len(df)

    stats["avg_upvotes"] = round(df["score_upvotes"].mean(), 2)

    stats["avg_comments"] = round(df["comments"].mean(), 2)

    stats["avg_engagement"] = round(df["engagement"].mean(), 2)

    stats["max_upvotes"] = int(df["score_upvotes"].max())

    stats["max_engagement"] = int(df["engagement"].max())

    return stats


# ================= BEST POSTS =================

def best_posts(df):

    best_upvote = df.loc[df["score_upvotes"].idxmax()]

    best_engagement = df.loc[df["engagement"].idxmax()]

    return best_upvote, best_engagement


# ================= TIME ANALYSIS =================

def time_analysis(df):

    hour_stats = df.groupby("hour")["engagement"].mean().sort_values(ascending=False)

    day_stats = df.groupby("day")["engagement"].mean().sort_values(ascending=False)

    return hour_stats, day_stats


# ================= SUBREDDIT ANALYSIS =================

def subreddit_analysis(df):

    sub_stats = df.groupby("subreddit").agg({
        "score_upvotes": "mean",
        "comments": "mean",
        "engagement": "mean",
        "post_id": "count"
    }).sort_values("engagement", ascending=False)

    return sub_stats


# ================= REPORT =================

def generate_report(df, stats, best_upvote, best_engagement,
                    hour_stats, day_stats, sub_stats):

    with open(REPORT_FILE, "w", encoding="utf-8") as f:

        f.write("===== REDDIT USER ANALYTICS REPORT =====\n\n")

        f.write(f"Total Posts: {stats['total_posts']}\n")
        f.write(f"Average Upvotes: {stats['avg_upvotes']}\n")
        f.write(f"Average Comments: {stats['avg_comments']}\n")
        f.write(f"Average Engagement: {stats['avg_engagement']}\n\n")

        f.write("----- TOP PERFORMING POSTS -----\n\n")

        f.write("Best by Upvotes:\n")
        f.write(f"Title: {best_upvote['title']}\n")
        f.write(f"Upvotes: {best_upvote['score_upvotes']}\n")
        f.write(f"Subreddit: {best_upvote['subreddit']}\n")
        f.write(f"Link: {best_upvote['permalink']}\n\n")

        f.write("Best by Engagement:\n")
        f.write(f"Title: {best_engagement['title']}\n")
        f.write(f"Engagement: {best_engagement['engagement']}\n")
        f.write(f"Subreddit: {best_engagement['subreddit']}\n")
        f.write(f"Link: {best_engagement['permalink']}\n\n")

        f.write("----- BEST POSTING HOURS (Avg Engagement) -----\n\n")

        for hour, val in hour_stats.items():
            f.write(f"{hour:02d}:00 - {round(val,2)}\n")

        f.write("\n----- BEST DAYS (Avg Engagement) -----\n\n")

        for day, val in day_stats.items():
            f.write(f"{day}: {round(val,2)}\n")

        f.write("\n----- SUBREDDIT PERFORMANCE -----\n\n")

        f.write(sub_stats.to_string())

    print(f"[SUCCESS] Report generated → {REPORT_FILE}")


# ================= VISUALIZATION =================

def generate_plots(df):

    # Hour vs Engagement
    plt.figure()
    df.groupby("hour")["engagement"].mean().plot()
    plt.title("Average Engagement by Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Engagement")
    plt.savefig("hour_engagement.png")
    plt.close()

    # Day vs Engagement
    plt.figure()
    df.groupby("day")["engagement"].mean().plot(kind="bar")
    plt.title("Average Engagement by Day")
    plt.xlabel("Day")
    plt.ylabel("Engagement")
    plt.savefig("day_engagement.png")
    plt.close()

    print("[SUCCESS] Charts saved: hour_engagement.png, day_engagement.png")


# ================= MAIN =================

def main():

    df = load_data()

    stats = basic_stats(df)

    best_upvote, best_engagement = best_posts(df)

    hour_stats, day_stats = time_analysis(df)

    sub_stats = subreddit_analysis(df)

    generate_report(
        df, stats, best_upvote, best_engagement,
        hour_stats, day_stats, sub_stats
    )

    generate_plots(df)


if __name__ == "__main__":
    main()