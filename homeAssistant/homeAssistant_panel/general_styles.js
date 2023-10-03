import { css } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

export const generalStyles = css`
    .SingleEntry{
        width: 542px;
        height: 72px;
        display: flex;
        padding-left: 20px;
        padding-right: 20px;
        align-content: center;
        flex-wrap: wrap;
    }
    
    .description{
        height: 19px;
        padding-right: 20px;
        margin-top: auto;
        margin-bottom: auto;
    }

    .card{
        border-style: none;
        width: var(--card-width);
        display: flex;
        flex-wrap: wrap;
        align-content: flex-start;
        justify-content: center;
    }
    
    ha-card{
        border-left-style: var(--side-bd);
        border-right-style: var(--side-bd);
    }
`;